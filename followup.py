"""AI follow-up message generator for stale applications."""

import json
from datetime import datetime
from pathlib import Path

from config import RESUME_CONTEXT
from llm import GEMINI_QUALITY, gemini_json, perplexity_search

FOLLOWUPS_FILE = Path(__file__).parent / "data" / "followups.json"


def _load_followups() -> list:
    if not FOLLOWUPS_FILE.exists():
        return []
    with open(FOLLOWUPS_FILE) as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _save_followups(data: list):
    with open(FOLLOWUPS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _fetch_company_news(company: str) -> dict:
    """Fetch recent company news via Perplexity. Never raises."""
    query = (
        f"Find up to 3 notable news highlights about {company} from the last ~60 days — "
        "product launches, funding rounds, milestones, or leadership hires. "
        "Return ONLY valid JSON matching this exact schema, no prose or markdown: "
        '{"highlights": [{"headline": "<short>", "date": "<YYYY-MM-DD or month year>", '
        '"summary": "<1-2 sentence summary>"}]} '
        "Return empty highlights array if nothing notable."
    )
    try:
        result = perplexity_search(query, model="sonar", max_tokens=600)
        content = result.get("content") or {}
        if not isinstance(content, dict) or not content.get("highlights"):
            return {"highlights": []}
        return content
    except Exception:
        return {"highlights": []}


def generate_followup(application: dict, days_since: int) -> dict:
    """Generate a follow-up message for a stale application."""
    if days_since < 14:
        followup_num = "first"
        angle = "Express continued interest. Reference something specific about the company."
    elif days_since < 21:
        followup_num = "second"
        angle = "Try a different angle — mention a recent company milestone, product launch, or news."
    else:
        followup_num = "third"
        angle = "This is a last check-in. Be gracious. Suggest staying in touch for future opportunities."

    news = _fetch_company_news(application.get("company", ""))
    highlights = news.get("highlights") or []
    if not highlights:
        news_context = (
            "No recent notable news found — write a warm, sincere check-in that references "
            "something about the company's public mission or products."
        )
    else:
        top = highlights[:2]
        lines = []
        for h in top:
            headline = h.get("headline", "").strip()
            date = h.get("date", "").strip()
            summary = h.get("summary", "").strip()
            lines.append(f"- {headline} ({date}): {summary}")
        news_context = "\n".join(lines)

    prompt = f"""Generate a {followup_num} follow-up message for a job application.

CANDIDATE:
{RESUME_CONTEXT}

APPLICATION:
- Company: {application.get('company', 'Unknown')}
- Role: {application.get('role', 'Unknown')}
- Applied: {application.get('applied_date', 'Unknown')}
- Days since application: {days_since}
- Status: {application.get('status', 'applied')}

RECENT COMPANY NEWS (use to make this feel timely — reference a specific launch/milestone/hire if relevant):
{news_context}

INSTRUCTIONS:
- {angle}
- If recent news is provided above, lead with it ("I saw you launched X last week..."). Never fabricate news — only use what's provided.
- Tone: Warm, shows continued interest. Never desperate. Never "just checking in".
- Always add value — reference something relevant about the company.
- Keep it brief and professional.
- DO NOT mention "RAG pipelines".

Return ONLY valid JSON:
{{
    "followup_email": "Subject: ...\\n\\n<the email body>",
    "followup_linkedin": "<2-3 sentence LinkedIn follow-up>",
    "company_news_used": "<short string describing which news item was referenced, or 'none'>",
    "suggested_action": "<one of: follow_up | try_different_contact | move_on>"
}}"""

    try:
        result = gemini_json(prompt, model=GEMINI_QUALITY, max_tokens=1000)
        result.setdefault("company_news_used", "none")
    except Exception as e:
        result = {
            "followup_email": f"Error generating follow-up: {e}",
            "followup_linkedin": f"Error: {e}",
            "company_news_used": "none",
            "suggested_action": "follow_up",
        }

    if days_since >= 21:
        result["suggested_action"] = "move_on"
    elif days_since >= 14:
        result["suggested_action"] = "try_different_contact"

    return result


def save_followup(app_id: str, followup: dict):
    """Save a generated follow-up message."""
    data = _load_followups()
    entry = {
        "app_id": app_id,
        "generated_date": datetime.now().strftime("%Y-%m-%d"),
        **followup,
    }
    found = False
    for i, item in enumerate(data):
        if item.get("app_id") == app_id:
            data[i] = entry
            found = True
            break
    if not found:
        data.append(entry)
    _save_followups(data)


def get_followup(app_id: str) -> dict | None:
    """Load saved follow-up for an application."""
    for item in _load_followups():
        if item.get("app_id") == app_id:
            return item
    return None


def auto_generate_followups(applications: list) -> list:
    """Auto-generate follow-ups for stale applications."""
    today = datetime.now().date()
    generated = []

    for app in applications:
        if app["status"] not in ("applied", "referral_sent"):
            continue
        if not app.get("applied_date"):
            continue

        applied_date = datetime.strptime(app["applied_date"], "%Y-%m-%d").date()
        days_since = (today - applied_date).days

        if days_since not in range(6, 23):
            continue

        existing = get_followup(app["id"])
        if existing and existing.get("generated_date") == today.strftime("%Y-%m-%d"):
            continue

        followup = generate_followup(app, days_since)
        save_followup(app["id"], followup)
        generated.append((app, followup))

    return generated
