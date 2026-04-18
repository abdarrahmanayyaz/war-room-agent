"""3-layer job search engine powered by Perplexity Sonar."""

import hashlib
import json
import re
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

from config import WAR_PLAN
from llm import perplexity_search

DATA_DIR = Path(__file__).parent / "data"
SCOUTED_FILE = DATA_DIR / "scouted.json"
ATS_CACHE_DIR = DATA_DIR / ".ats_cache"
ATS_CACHE_TTL_SECONDS = 24 * 60 * 60

DELAY = 1
MAX_QUERIES = 40

HEADERS = {"User-Agent": "WarRoom/1.0"}

ATS_MAP = {
    "lever": {
        "base": "https://api.lever.co/v0/postings/{slug}?mode=json",
        "companies": {},
    },
    "greenhouse": {
        "base": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
        "companies": {
            "Anthropic": "anthropic",
            "Vercel": "vercel",
            "Scale AI": "scaleai",
            "Datadog": "datadog",
            "Cloudflare": "cloudflare",
            "GitLab": "gitlab",
            "Stripe": "stripe",
            "MongoDB": "mongodb",
        },
    },
    "ashby": {
        "base": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
        "companies": {},
    },
}

ROLE_CLASSIFIERS = {
    "FDE": ["forward deployed", "field engineer", "customer engineer"],
    "AI Solutions": ["solutions engineer", "solutions architect", "AI solutions"],
    "Applied AI": ["applied ai", "applied ml", "AI engineer", "ml engineer", "machine learning engineer"],
    "DevRel": ["developer relations", "developer advocate", "dev rel", "developer experience", "devrel"],
    "Startup AI": ["founding engineer", "startup", "early stage"],
}

EXCLUDE_PATTERNS = [
    r"\bphd\s+required\b",
    r"\b(?:10|11|12|13|14|15)\+?\s*(?:years|yrs)\b",
    r"\b8\+\s*(?:years|yrs)\b",
    r"\bintern(?:ship)?\b",
    r"\bts[/-]sci\b",
    r"\btop\s+secret\b",
    r"\bwet\s+lab\b",
]

INCLUDE_PATTERNS = [
    r"\bai\b", r"\bllm\b", r"\bml\b", r"\bmachine\s+learning\b",
    r"\bgenerative\b", r"\bagentic\b", r"\bsolutions\s+engineer\b",
    r"\bforward\s+deployed\b", r"\bdeveloper\s+relations\b",
    r"\bdeveloper\s+advocate\b", r"\bapplied\s+ai\b", r"\bai\s+platform\b",
    r"\bdev\s*rel\b",
]


def _job_hash(company: str, role: str, url: str) -> str:
    raw = f"{company.lower().strip()}|{role.lower().strip()}|{url.strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_scouted() -> list:
    if not SCOUTED_FILE.exists():
        return []
    with open(SCOUTED_FILE) as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def save_scouted(jobs: list):
    with open(SCOUTED_FILE, "w") as f:
        json.dump(jobs, f, indent=2, default=str)


def _existing_hashes() -> set:
    return {j.get("hash", "") for j in load_scouted()}


def _classify_tier(company: str) -> int:
    name = company.lower().strip()
    for c in WAR_PLAN["tier_1"]:
        if c.lower() in name or name in c.lower():
            return 1
    for c in WAR_PLAN["tier_2"]:
        if c.lower() in name or name in c.lower():
            return 2
    for c in WAR_PLAN["tier_3"]:
        if c.lower() in name or name in c.lower():
            return 3
    return 0


def _classify_role(title: str) -> str:
    t = title.lower()
    for role_type, keywords in ROLE_CLASSIFIERS.items():
        if any(kw in t for kw in keywords):
            return role_type
    return "AI Engineer"


def _detect_remote(text: str) -> str:
    t = text.lower()
    if "remote" in t and "hybrid" not in t:
        return "Full"
    if "hybrid" in t:
        return "Hybrid"
    if "on-site" in t or "onsite" in t or "in-office" in t:
        return "On-site"
    return "Full"


def _should_exclude(text: str) -> bool:
    t = text.lower()
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, t, re.IGNORECASE):
            return True
    return False


def _has_relevant_keyword(text: str) -> bool:
    t = text.lower()
    for pat in INCLUDE_PATTERNS:
        if re.search(pat, t, re.IGNORECASE):
            return True
    return False


TITLE_PATTERNS = [
    r"\bforward\s+deployed\b",
    r"\bsolutions?\s+(?:engineer|architect)\b",
    r"\bapplied\s+(?:ai|ml|machine\s+learning)\b",
    r"\bdeveloper\s+(?:relations|advocate|experience)\b",
    r"\bdev\s*rel\b",
    r"\bai\s+(?:engineer|solutions?)\b",
    r"\b(?:ml|machine\s+learning|llm|genai|generative\s+ai|agentic|ai\s+platform|ai\s+product|ai\s+research)\s+engineer\b",
    r"\bfounding\s+engineer\b",
    r"\bfield\s+engineer\b",
    r"\bcustomer\s+engineer\b",
    r"\b(?:research\s+engineer|research\s+scientist)\b.*\b(?:ml|ai|llm)\b",
]


def _title_matches_target(title: str) -> bool:
    """Strict role-title match — used by Layer 0 direct APIs where snippets contain boilerplate."""
    t = title.lower()
    for pat in TITLE_PATTERNS:
        if re.search(pat, t, re.IGNORECASE):
            return True
    return False


def _source_from_url(url: str) -> str:
    for s in ["lever.co", "greenhouse.io", "ashbyhq.com", "wellfound.com",
              "builtin.com", "ycombinator.com", "linkedin.com"]:
        if s in url:
            return s.split(".")[0]
    try:
        host = urlparse(url).hostname or ""
        return host.replace("www.", "").split(".")[0] or "web"
    except Exception:
        return "web"


SONAR_SCHEMA_INSTRUCTIONS = """Return ONLY valid JSON of this shape:
{
  "jobs": [
    {
      "company": "<company name>",
      "role": "<exact role title>",
      "url": "<direct application/job-post URL>",
      "remote": "<Full|Hybrid|On-site>",
      "snippet": "<1-2 sentences from the posting>"
    }
  ]
}
Rules:
- Only include CURRENT, OPEN roles posted in the last 60 days.
- Prefer direct postings on lever.co, greenhouse.io, ashbyhq.com, or the company's career site.
- Skip aggregator/listicle pages ("Top 10 jobs", "Hiring now" roundups).
- Skip internships, PhD-required, 8+ yrs required, and clearance-only roles.
- If you cannot find any, return {"jobs": []}."""


def _sonar_find_jobs(query: str, *, max_tokens: int = 1800) -> list[dict]:
    """Ask Perplexity Sonar for job postings matching the query."""
    full_query = f"{query}\n\n{SONAR_SCHEMA_INSTRUCTIONS}"
    try:
        data = perplexity_search(full_query, model="sonar", max_tokens=max_tokens)
    except Exception as e:
        print(f"[scout] perplexity error for '{query[:60]}...': {e}", file=sys.stderr)
        return []
    content = data.get("content", {}) or {}
    jobs = content.get("jobs", []) if isinstance(content, dict) else []
    return jobs if isinstance(jobs, list) else []


def _process_sonar_jobs(
    raw_jobs: list[dict],
    existing_hashes: set,
    discovery_type: str,
) -> list[dict]:
    """Normalize Sonar job objects into tracker-compatible dicts."""
    jobs = []
    for r in raw_jobs:
        if not isinstance(r, dict):
            continue
        company = (r.get("company") or "").strip()
        role = (r.get("role") or "").strip()
        url = (r.get("url") or "").strip()
        snippet = (r.get("snippet") or "").strip()

        if not company or not role or not url:
            continue
        if not url.startswith("http"):
            continue

        full_text = f"{role} {snippet}"
        if not _has_relevant_keyword(full_text):
            continue
        if _should_exclude(full_text):
            continue
        if len(role) > 80:
            continue

        h = _job_hash(company, role, url)
        if h in existing_hashes:
            continue
        existing_hashes.add(h)

        remote = r.get("remote") or _detect_remote(full_text)
        if remote not in ("Full", "Hybrid", "On-site"):
            remote = _detect_remote(full_text)

        jobs.append({
            "id": str(uuid.uuid4()),
            "company": company,
            "role": role,
            "tier": _classify_tier(company),
            "role_type": _classify_role(role),
            "remote": remote,
            "url": url,
            "source": _source_from_url(url),
            "scouted_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "new",
            "discovery": discovery_type,
            "hash": h,
            "snippet": snippet[:300],
            "score": None,
            "score_reasoning": None,
            "score_strengths": None,
            "score_gaps": None,
        })
    return jobs


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"&nbsp;|&#160;", " ", clean)
    clean = re.sub(r"&amp;", "&", clean)
    clean = re.sub(r"&lt;", "<", clean)
    clean = re.sub(r"&gt;", ">", clean)
    clean = re.sub(r"&quot;", '"', clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _cache_path(platform: str, slug: str) -> Path:
    """Return the cache file path for a given platform/slug."""
    ATS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return ATS_CACHE_DIR / f"{platform}_{slug}.json"


def _cache_read(platform: str, slug: str):
    """Return cached payload if < 24h old, else None."""
    path = _cache_path(platform, slug)
    if not path.exists():
        return None
    age = (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).total_seconds()
    if age >= ATS_CACHE_TTL_SECONDS:
        return None
    with open(path) as f:
        return json.load(f)


def _cache_write(platform: str, slug: str, payload):
    """Persist payload to the ATS cache."""
    path = _cache_path(platform, slug)
    with open(path, "w") as f:
        json.dump(payload, f)


def _fetch_lever(slug: str) -> list[dict]:
    """Fetch raw Lever postings for a company slug."""
    cached = _cache_read("lever", slug)
    if cached is not None:
        return cached
    url = ATS_MAP["lever"]["base"].format(slug=slug)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[scout] lever fetch failed for {slug}: {e}", file=sys.stderr)
        return []
    jobs = data if isinstance(data, list) else []
    _cache_write("lever", slug, jobs)
    return jobs


def _fetch_greenhouse(slug: str) -> list[dict]:
    """Fetch raw Greenhouse postings for a board slug."""
    cached = _cache_read("greenhouse", slug)
    if cached is not None:
        return cached
    url = ATS_MAP["greenhouse"]["base"].format(slug=slug)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[scout] greenhouse fetch failed for {slug}: {e}", file=sys.stderr)
        return []
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    _cache_write("greenhouse", slug, jobs)
    return jobs


def _fetch_ashby(slug: str) -> list[dict]:
    """Fetch raw Ashby postings for a job-board slug."""
    cached = _cache_read("ashby", slug)
    if cached is not None:
        return cached
    url = ATS_MAP["ashby"]["base"].format(slug=slug)
    try:
        resp = requests.post(url, headers=HEADERS, json={}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[scout] ashby fetch failed for {slug}: {e}", file=sys.stderr)
        return []
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    _cache_write("ashby", slug, jobs)
    return jobs


def _normalize_lever(company: str, raw: list[dict], existing_hashes: set) -> list[dict]:
    """Convert Lever postings into tracker-compatible dicts."""
    out = []
    for r in raw:
        if not isinstance(r, dict):
            continue
        role = (r.get("text") or "").strip()
        url = (r.get("hostedUrl") or "").strip()
        if not role or not url or not url.startswith("http"):
            continue
        snippet = r.get("descriptionPlain") or _strip_html(r.get("description") or "")
        snippet = snippet.strip()
        location = ""
        cats = r.get("categories") or {}
        if isinstance(cats, dict):
            location = cats.get("location") or ""
        if not _title_matches_target(role):
            continue
        full_text = f"{role} {snippet} {location}"
        if _should_exclude(full_text):
            continue
        if len(role) > 80:
            continue
        h = _job_hash(company, role, url)
        if h in existing_hashes:
            continue
        existing_hashes.add(h)
        remote = _detect_remote(f"{location} {snippet}")
        out.append({
            "id": str(uuid.uuid4()),
            "company": company,
            "role": role,
            "tier": _classify_tier(company),
            "role_type": _classify_role(role),
            "remote": remote,
            "url": url,
            "source": "direct_api",
            "scouted_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "new",
            "discovery": "direct_api",
            "hash": h,
            "snippet": snippet[:300],
            "score": None,
            "score_reasoning": None,
            "score_strengths": None,
            "score_gaps": None,
        })
    return out


def _normalize_greenhouse(company: str, raw: list[dict], existing_hashes: set) -> list[dict]:
    """Convert Greenhouse postings into tracker-compatible dicts."""
    out = []
    for r in raw:
        if not isinstance(r, dict):
            continue
        role = (r.get("title") or "").strip()
        url = (r.get("absolute_url") or "").strip()
        if not role or not url or not url.startswith("http"):
            continue
        snippet = _strip_html(r.get("content") or "").strip()
        loc = r.get("location") or {}
        location = loc.get("name", "") if isinstance(loc, dict) else ""
        if not _title_matches_target(role):
            continue
        full_text = f"{role} {snippet} {location}"
        if _should_exclude(full_text):
            continue
        if len(role) > 80:
            continue
        h = _job_hash(company, role, url)
        if h in existing_hashes:
            continue
        existing_hashes.add(h)
        remote = _detect_remote(f"{location} {snippet}")
        out.append({
            "id": str(uuid.uuid4()),
            "company": company,
            "role": role,
            "tier": _classify_tier(company),
            "role_type": _classify_role(role),
            "remote": remote,
            "url": url,
            "source": "direct_api",
            "scouted_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "new",
            "discovery": "direct_api",
            "hash": h,
            "snippet": snippet[:300],
            "score": None,
            "score_reasoning": None,
            "score_strengths": None,
            "score_gaps": None,
        })
    return out


def _normalize_ashby(company: str, raw: list[dict], existing_hashes: set) -> list[dict]:
    """Convert Ashby postings into tracker-compatible dicts."""
    out = []
    for r in raw:
        if not isinstance(r, dict):
            continue
        role = (r.get("title") or "").strip()
        url = (r.get("jobUrl") or r.get("applicationUrl") or "").strip()
        if not role or not url or not url.startswith("http"):
            continue
        snippet = (r.get("descriptionPlain") or "").strip()
        loc = r.get("location") or ""
        location = loc if isinstance(loc, str) else ""
        if not _title_matches_target(role):
            continue
        full_text = f"{role} {snippet} {location}"
        if _should_exclude(full_text):
            continue
        if len(role) > 80:
            continue
        h = _job_hash(company, role, url)
        if h in existing_hashes:
            continue
        existing_hashes.add(h)
        remote = _detect_remote(f"{location} {snippet}")
        out.append({
            "id": str(uuid.uuid4()),
            "company": company,
            "role": role,
            "tier": _classify_tier(company),
            "role_type": _classify_role(role),
            "remote": remote,
            "url": url,
            "source": "direct_api",
            "scouted_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "new",
            "discovery": "direct_api",
            "hash": h,
            "snippet": snippet[:300],
            "score": None,
            "score_reasoning": None,
            "score_strengths": None,
            "score_gaps": None,
        })
    return out


def _run_layer_zero(existing_hashes: set, progress_callback=None) -> list[dict]:
    """Fetch jobs from all ATS APIs. Returns normalized job dicts."""
    results = []
    pairs = []
    for platform, cfg in ATS_MAP.items():
        for company, slug in cfg["companies"].items():
            pairs.append((platform, company, slug))
    total = len(pairs) or 1
    for idx, (platform, company, slug) in enumerate(pairs):
        if platform == "lever":
            raw = _fetch_lever(slug)
            normalized = _normalize_lever(company, raw, existing_hashes)
        elif platform == "greenhouse":
            raw = _fetch_greenhouse(slug)
            normalized = _normalize_greenhouse(company, raw, existing_hashes)
        elif platform == "ashby":
            raw = _fetch_ashby(slug)
            normalized = _normalize_ashby(company, raw, existing_hashes)
        else:
            normalized = []
        results.extend(normalized)
        if progress_callback:
            pct = 0.0 + 0.05 * (idx + 1) / total
            progress_callback(
                f"Layer 0: {idx+1}/{total} ATS APIs — {len(results)} direct postings",
                pct,
            )
    return results


def _build_named_queries() -> list[str]:
    """Layer 1: One query per target company."""
    queries = []
    all_companies = WAR_PLAN["tier_1"] + WAR_PLAN["tier_2"] + WAR_PLAN["tier_3"]
    roles = ", ".join(WAR_PLAN["target_roles"])
    for company in all_companies:
        queries.append(
            f"Find up to 8 open, remote-friendly job postings at {company} for any of these roles: "
            f"{roles}. Return the direct application URL for each."
        )
    return queries


def _build_broad_queries() -> list[str]:
    """Layer 2: Cross-company role sweeps."""
    return [
        "Find recent remote AI Solutions Engineer openings (posted in last 60 days).",
        "Find recent remote Forward Deployed Engineer openings at AI or infra companies.",
        "Find remote Applied AI Engineer roles open to candidates with 1-5 years experience.",
        "Find Developer Relations / Developer Advocate roles at LLM / AI platform companies, remote-friendly.",
        "Find remote Solutions Architect roles focused on AI / generative AI / LLMs.",
        "Find founding engineer / early-stage AI startup engineering roles, remote-friendly.",
    ]


def _build_aggregator_queries() -> list[str]:
    """Layer 3: Job-board focused sweeps."""
    return [
        "Find AI engineer roles on wellfound.com that are remote and open now.",
        "Find AI solutions engineer roles on lever.co career pages, remote.",
        "Find forward deployed engineer roles on greenhouse.io career pages, remote.",
        "Find AI / LLM engineer roles on jobs.ashbyhq.com, remote-friendly.",
        "Find AI engineering roles from Y Combinator companies (ycombinator.com/companies), remote-friendly.",
    ]


def run_scout(
    wide_net: bool = True,
    progress_callback=None,
) -> list[dict]:
    """Run the full 3-layer scout pipeline via Perplexity Sonar."""
    existing_hashes = _existing_hashes()
    all_new_jobs = []
    query_count = 0

    def _report(msg, pct):
        if progress_callback:
            progress_callback(msg, pct)

    _report("Layer 0: Hitting direct ATS APIs...", 0.0)
    layer_zero_jobs = _run_layer_zero(existing_hashes, progress_callback=_report)
    all_new_jobs.extend(layer_zero_jobs)
    _report(f"Layer 0 done: {len(layer_zero_jobs)} direct-API postings", 0.05)

    named_queries = _build_named_queries()
    _report("Layer 1: Searching named target companies...", 0.05)
    for i, q in enumerate(named_queries):
        if query_count >= MAX_QUERIES:
            break
        raw = _sonar_find_jobs(q)
        jobs = _process_sonar_jobs(raw, existing_hashes, "named")
        all_new_jobs.extend(jobs)
        query_count += 1
        _report(f"Layer 1: {i+1}/{len(named_queries)} queries — {len(all_new_jobs)} roles found",
                0.05 + 0.3 * (i+1) / len(named_queries))
        time.sleep(DELAY)

    if wide_net:
        broad_queries = _build_broad_queries()
        _report("Layer 2: Broad role sweep...", 0.35)
        for i, q in enumerate(broad_queries):
            if query_count >= MAX_QUERIES:
                break
            raw = _sonar_find_jobs(q)
            jobs = _process_sonar_jobs(raw, existing_hashes, "broad_sweep")
            all_new_jobs.extend(jobs)
            query_count += 1
            _report(f"Layer 2: {i+1}/{len(broad_queries)} queries — {len(all_new_jobs)} roles found",
                    0.35 + 0.35 * (i+1) / len(broad_queries))
            time.sleep(DELAY)

        agg_queries = _build_aggregator_queries()
        _report("Layer 3: Checking job boards...", 0.70)
        for i, q in enumerate(agg_queries):
            if query_count >= MAX_QUERIES:
                break
            raw = _sonar_find_jobs(q)
            jobs = _process_sonar_jobs(raw, existing_hashes, "aggregator")
            all_new_jobs.extend(jobs)
            query_count += 1
            _report(f"Layer 3: {i+1}/{len(agg_queries)} queries — {len(all_new_jobs)} roles found",
                    0.70 + 0.25 * (i+1) / len(agg_queries))
            time.sleep(DELAY)

    remote_order = {"Full": 0, "Hybrid": 1, "On-site": 2}
    all_new_jobs.sort(key=lambda j: (
        0 if j.get("source") == "direct_api" else 1,
        remote_order.get(j["remote"], 2),
        j["tier"] if j["tier"] > 0 else 4,
    ))

    existing = load_scouted()
    existing.extend(all_new_jobs)
    save_scouted(existing)

    _report(f"Done! Found {len(all_new_jobs)} new roles.", 1.0)

    from tracker import log_activity
    log_activity("scout_completed", {
        "new_roles": len(all_new_jobs),
        "queries_run": query_count,
        "wide_net": wide_net,
        "layer_zero_jobs": len(layer_zero_jobs),
    })

    return all_new_jobs


def update_scouted_job(job_id: str, **kwargs):
    """Update a scouted job entry."""
    jobs = load_scouted()
    for j in jobs:
        if j["id"] == job_id:
            for k, v in kwargs.items():
                j[k] = v
            save_scouted(jobs)
            return j
    return None


if __name__ == "__main__":
    auto = "--auto" in sys.argv
    print("WAR ROOM SCOUT — Starting...")
    new_jobs = run_scout(wide_net=WAR_PLAN["wide_net"])
    print(f"Found {len(new_jobs)} new roles.")

    if auto and new_jobs:
        import subprocess
        high_score = len([j for j in new_jobs if (j.get("score") or 0) >= 8])
        msg = f"Found {len(new_jobs)} new roles"
        if high_score:
            msg += f" ({high_score} scored 8+)"
        msg += ". Open app to review."
        subprocess.run([
            "osascript", "-e",
            f'display notification "{msg}" with title "War Room"',
        ], check=False)
