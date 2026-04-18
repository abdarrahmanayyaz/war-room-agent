"""First-run onboarding wizard for War Room Agent."""

import json
import os
import re
from datetime import date

import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_LOCAL_PATH = os.path.join(PROJECT_ROOT, "config_local.py")
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

DEFAULT_ROLE_OPTIONS = [
    "Forward Deployed Engineer",
    "AI Solutions Engineer",
    "Applied AI Engineer",
    "Developer Relations Engineer",
    "Solutions Architect AI",
    "Founding Engineer",
]

TONE_OPTIONS = [
    "Warm, relationship-first",
    "Direct and concise",
    "Technical and detailed",
]


def needs_onboarding() -> bool:
    """True if config_local.py is missing in project root."""
    return not os.path.exists(CONFIG_LOCAL_PATH)


def _default_wizard_data() -> dict:
    """Seed the session-state data dict."""
    return {
        # profile
        "name": "",
        "email": "",
        "phone": "",
        "linkedin": "",
        "github": "",
        "website": "",
        # resume
        "resume_text": "",
        "headline": "",
        "differentiators": "",
        "skills": "",
        "education": "",
        # targets
        "target_roles": list(DEFAULT_ROLE_OPTIONS[:4]),
        "tier_1": "",
        "tier_2": "",
        "tier_3": "",
        "target_comp": "$200K+",
        "remote_preference": True,
        "weekly_target": 10,
        "min_experience_years": 0,
        "max_experience_years": 5,
        "plan_days": 60,
        "start_date": date.today().isoformat(),
        # tone & rules
        "tone": TONE_OPTIONS[0],
        "hard_rules": "",
        # api keys
        "gemini_key": os.environ.get("GEMINI_API_KEY", ""),
        "perplexity_key": os.environ.get("PERPLEXITY_API_KEY", ""),
        "gemini_ok": False,
        "perplexity_ok": False,
        "skip_tests": False,
    }


def _extract_pdf_text(file_bytes: bytes) -> str:
    """Parse PDF bytes to text via pymupdf."""
    import fitz  # noqa: F401 — import errors caught by caller
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    parts = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return "\n".join(parts).strip()


def _gemini_extract(resume_text: str) -> dict:
    """Ask Gemini Flash for differentiators, skills, and education."""
    from llm import gemini_json, GEMINI_FAST

    prompt = (
        "You are helping a candidate build their outreach profile. Read the resume "
        "below and return STRICT JSON with this exact schema:\n"
        '{"differentiators": ["<one differentiator with a concrete metric>", ...], '
        '"skills": "<comma-separated list>", '
        '"education": "<single line: degree, school, honors>"}\n\n'
        "Return 4 to 6 differentiators. Each one should be a single sentence that "
        "leads with the outcome, includes numbers where possible, and reads like a "
        "resume bullet. No markdown, no commentary.\n\n"
        "RESUME:\n" + resume_text
    )
    return gemini_json(prompt, model=GEMINI_FAST, max_tokens=1500)


def _build_resume_context(data: dict) -> str:
    """Render the RESUME_CONTEXT string in the spec's exact shape."""
    headline = data.get("headline", "").strip() or "Current Role"
    name = data.get("name", "").strip() or "Your Name"

    raw = data.get("differentiators", "").strip()
    items = [line.strip("-* \t") for line in raw.splitlines() if line.strip()]
    if not items:
        items = ["<Add your top differentiator>"]
    numbered = "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))

    skills = data.get("skills", "").strip() or "<skills>"
    education = data.get("education", "").strip() or "<education>"
    tone = data.get("tone", TONE_OPTIONS[0]).strip()
    rules = data.get("hard_rules", "").strip() or "buzzwords you dislike"

    text = (
        f"{name} — {headline}\n"
        f"\n"
        f"KEY DIFFERENTIATORS (use 1-2 most relevant per role):\n"
        f"\n"
        f"{numbered}\n"
        f"\n"
        f"SKILLS: {skills}\n"
        f"\n"
        f"EDUCATION: {education}\n"
        f"\n"
        f"TONE: {tone}.\n"
        f"\n"
        f"DO NOT mention {rules}."
    )
    return text


def _split_lines(text: str) -> list[str]:
    """Parse a newline-separated list, trimming blanks."""
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def _build_war_plan(data: dict) -> dict:
    """Render the WAR_PLAN dict."""
    return {
        "target_roles": list(data.get("target_roles", [])),
        "tier_1": _split_lines(data.get("tier_1", "")),
        "tier_2": _split_lines(data.get("tier_2", "")),
        "tier_3": _split_lines(data.get("tier_3", "")),
        "keywords": [
            "AI engineer", "LLM", "agentic", "forward deployed",
            "solutions engineer", "developer advocate",
        ],
        "remote_preference": "remote-first" if data.get("remote_preference") else "hybrid-ok",
        "wide_net": True,
        "target_comp": data.get("target_comp", "").strip(),
        "weekly_target": int(data.get("weekly_target", 10)),
        "min_experience_years": int(data.get("min_experience_years", 0)),
        "max_experience_years": int(data.get("max_experience_years", 5)),
        "start_date": str(data.get("start_date", date.today().isoformat())),
        "plan_days": int(data.get("plan_days", 60)),
    }


def _build_contact_info(data: dict) -> dict:
    """Render the CONTACT_INFO dict."""
    return {
        "name": data.get("name", "").strip(),
        "email": data.get("email", "").strip(),
        "phone": data.get("phone", "").strip(),
        "linkedin": data.get("linkedin", "").strip(),
        "github": data.get("github", "").strip(),
        "website": data.get("website", "").strip(),
    }


def _write_config_local(war_plan: dict, resume_context: str, contact_info: dict) -> None:
    """Emit config_local.py with clean formatting."""
    safe_resume = resume_context.replace('"""', "'''")

    war_plan_json = json.dumps(war_plan, indent=4)
    contact_json = json.dumps(contact_info, indent=4)

    content = (
        '"""Personal War Room overrides — generated by the onboarding wizard."""\n'
        "\n"
        f"WAR_PLAN = {war_plan_json}\n"
        "\n"
        f'RESUME_CONTEXT = """\n{safe_resume}\n""".strip()\n'
        "\n"
        f"CONTACT_INFO = {contact_json}\n"
    )
    with open(CONFIG_LOCAL_PATH, "w") as f:
        f.write(content)


def _upsert_env(key: str, value: str) -> None:
    """Set KEY=value in .env, merging with existing content."""
    if not value:
        return
    existing = ""
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            existing = f.read()

    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    line = f"{key}={value}"
    if pattern.search(existing):
        new = pattern.sub(line, existing)
    else:
        sep = "" if existing.endswith("\n") or not existing else "\n"
        new = existing + sep + line + "\n"
    with open(ENV_PATH, "w") as f:
        f.write(new)


def _write_env(data: dict) -> None:
    """Upsert both API keys."""
    _upsert_env("GEMINI_API_KEY", data.get("gemini_key", "").strip())
    _upsert_env("PERPLEXITY_API_KEY", data.get("perplexity_key", "").strip())


# ── Individual step renderers ─────────────────────────────────────────

def _step_profile(data: dict) -> bool:
    """Step 1 — profile. Returns True if required fields filled."""
    st.subheader("Step 1 — Profile")
    st.caption("Tell us who you are. Name and email are required.")

    data["name"] = st.text_input("Full name *", value=data.get("name", ""))
    data["email"] = st.text_input("Email *", value=data.get("email", ""))
    data["phone"] = st.text_input("Phone", value=data.get("phone", ""))
    data["linkedin"] = st.text_input("LinkedIn URL", value=data.get("linkedin", ""))
    data["github"] = st.text_input("GitHub URL", value=data.get("github", ""))
    data["website"] = st.text_input("Portfolio / website URL", value=data.get("website", ""))

    return bool(data["name"].strip() and data["email"].strip())


def _step_resume(data: dict) -> bool:
    """Step 2 — resume. Returns True if we have resume text + differentiators."""
    st.subheader("Step 2 — Resume")
    st.caption("Upload a PDF or paste your resume. Gemini will extract differentiators.")

    mode = st.radio("Input method", ["Upload PDF", "Paste text"], horizontal=True, key="wiz_resume_mode")

    if mode == "Upload PDF":
        upload = st.file_uploader("Resume PDF", type=["pdf"], key="wiz_resume_pdf")
        if upload is not None:
            try:
                text = _extract_pdf_text(upload.getvalue())
                data["resume_text"] = text
                st.success(f"Parsed PDF — {len(text)} characters extracted.")
            except ImportError:
                st.error("pip install pymupdf to enable PDF upload, or paste resume text")
            except Exception as e:
                st.error(f"PDF parse failed: {e}")

    data["resume_text"] = st.text_area(
        "Resume text",
        value=data.get("resume_text", ""),
        height=300,
        key="wiz_resume_text",
    )

    data["headline"] = st.text_input(
        "Current role / headline (e.g., 'AI Engineer at Acme')",
        value=data.get("headline", ""),
    )

    if st.button("🪄 Extract differentiators with Gemini", disabled=not data["resume_text"].strip()):
        if not os.environ.get("GEMINI_API_KEY") and not data.get("gemini_key"):
            st.warning("No Gemini key set yet. Enter it in Step 5, then come back.")
        else:
            if data.get("gemini_key"):
                os.environ["GEMINI_API_KEY"] = data["gemini_key"].strip()
            try:
                with st.spinner("Gemini is reading your resume..."):
                    out = _gemini_extract(data["resume_text"])
                diffs = out.get("differentiators") or []
                data["differentiators"] = "\n".join(diffs)
                data["skills"] = out.get("skills", "")
                data["education"] = out.get("education", "")
                st.success("Extracted — review and edit below.")
            except Exception as e:
                st.error(f"Extraction failed: {e}")

    data["differentiators"] = st.text_area(
        "Differentiators (one per line)",
        value=data.get("differentiators", ""),
        height=200,
    )
    data["skills"] = st.text_input("Skills (comma-separated)", value=data.get("skills", ""))
    data["education"] = st.text_input("Education", value=data.get("education", ""))

    return bool(data["resume_text"].strip() and data["differentiators"].strip())


def _step_targets(data: dict) -> bool:
    """Step 3 — targets."""
    st.subheader("Step 3 — Targets")
    st.caption("Define the shape of your search.")

    data["target_roles"] = st.multiselect(
        "Target role types",
        options=DEFAULT_ROLE_OPTIONS,
        default=data.get("target_roles", DEFAULT_ROLE_OPTIONS[:4]),
    )
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        data["tier_1"] = st.text_area("Tier 1 companies (one per line)", value=data.get("tier_1", ""), height=150)
    with col_b:
        data["tier_2"] = st.text_area("Tier 2 companies (one per line)", value=data.get("tier_2", ""), height=150)
    with col_c:
        data["tier_3"] = st.text_area("Tier 3 companies (one per line)", value=data.get("tier_3", ""), height=150)

    data["target_comp"] = st.text_input("Target compensation", value=data.get("target_comp", "$200K+"))
    data["remote_preference"] = st.checkbox("Prefer remote", value=bool(data.get("remote_preference", True)))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        data["weekly_target"] = st.number_input(
            "Weekly target", min_value=1, max_value=100, value=int(data.get("weekly_target", 10)),
        )
    with col2:
        data["min_experience_years"] = st.number_input(
            "Min YoE", min_value=0, max_value=30, value=int(data.get("min_experience_years", 0)),
        )
    with col3:
        data["max_experience_years"] = st.number_input(
            "Max YoE", min_value=0, max_value=30, value=int(data.get("max_experience_years", 5)),
        )
    with col4:
        data["plan_days"] = st.number_input(
            "Plan length (days)", min_value=7, max_value=365, value=int(data.get("plan_days", 60)),
        )

    current_start = data.get("start_date", date.today().isoformat())
    try:
        default_date = date.fromisoformat(current_start)
    except Exception:
        default_date = date.today()
    picked = st.date_input("Start date", value=default_date)
    data["start_date"] = picked.isoformat()

    return bool(data["target_roles"])


def _step_tone(data: dict) -> bool:
    """Step 4 — tone & hard rules."""
    st.subheader("Step 4 — Tone & rules")
    st.caption("Shapes every outreach prompt going forward.")

    tone_idx = TONE_OPTIONS.index(data["tone"]) if data.get("tone") in TONE_OPTIONS else 0
    data["tone"] = st.radio("Outreach tone", TONE_OPTIONS, index=tone_idx)
    data["hard_rules"] = st.text_area(
        "Hard rules — things never to mention",
        value=data.get("hard_rules", ""),
        height=100,
        placeholder="e.g., Don't mention RAG pipelines. Avoid buzzwords.",
    )
    return True


def _test_gemini(key: str) -> tuple[bool, str]:
    """Tiny round-trip to verify the Gemini key."""
    if not key.strip():
        return False, "No key provided"
    old = os.environ.get("GEMINI_API_KEY", "")
    os.environ["GEMINI_API_KEY"] = key.strip()
    try:
        import llm
        llm._client = None  # reset cached client
        llm._GEMINI_KEY = key.strip()
        out = llm.gemini_json('Return {"ok": true}', max_tokens=64)
        if isinstance(out, dict) and out.get("ok") is True:
            return True, "Gemini OK"
        return True, f"Gemini responded: {out}"
    except Exception as e:
        return False, f"Gemini failed: {e}"
    finally:
        if old:
            os.environ["GEMINI_API_KEY"] = old


def _test_perplexity(key: str) -> tuple[bool, str]:
    """Tiny round-trip to verify the Perplexity key."""
    if not key.strip():
        return False, "No key provided"
    old = os.environ.get("PERPLEXITY_API_KEY", "")
    os.environ["PERPLEXITY_API_KEY"] = key.strip()
    try:
        from llm import perplexity_search
        perplexity_search(
            'Return JSON: {"ok": true}. No prose.',
            max_tokens=64,
        )
        return True, "Perplexity OK"
    except Exception as e:
        return False, f"Perplexity failed: {e}"
    finally:
        if old:
            os.environ["PERPLEXITY_API_KEY"] = old


def _step_keys(data: dict) -> bool:
    """Step 5 — API keys. Returns True when Finish is allowed."""
    st.subheader("Step 5 — API keys")
    st.caption("Stored locally in `.env`. Never committed.")

    data["gemini_key"] = st.text_input(
        "GEMINI_API_KEY", type="password", value=data.get("gemini_key", ""),
    )
    data["perplexity_key"] = st.text_input(
        "PERPLEXITY_API_KEY", type="password", value=data.get("perplexity_key", ""),
    )

    col_g, col_p = st.columns(2)
    with col_g:
        if st.button("Test Gemini"):
            ok, msg = _test_gemini(data["gemini_key"])
            data["gemini_ok"] = ok
            (st.success if ok else st.error)(msg)
    with col_p:
        if st.button("Test Perplexity"):
            ok, msg = _test_perplexity(data["perplexity_key"])
            data["perplexity_ok"] = ok
            (st.success if ok else st.error)(msg)

    data["skip_tests"] = st.checkbox(
        "Skip tests (I know what I'm doing)",
        value=bool(data.get("skip_tests", False)),
    )

    return bool(data["skip_tests"] or (data["gemini_ok"] and data["perplexity_ok"]))


# ── Public wizard ─────────────────────────────────────────────────────

def render_wizard() -> None:
    """Render the 5-step first-run onboarding wizard."""
    if "wizard_step" not in st.session_state:
        st.session_state["wizard_step"] = 1
    if "wizard_data" not in st.session_state:
        st.session_state["wizard_data"] = _default_wizard_data()

    step = st.session_state["wizard_step"]
    data = st.session_state["wizard_data"]

    with st.container():
        st.markdown("## 🔴 War Room — Setup")
        st.markdown(f"**Step {step} of 5**")
        st.progress(step / 5)

        if step == 1:
            can_advance = _step_profile(data)
        elif step == 2:
            can_advance = _step_resume(data)
        elif step == 3:
            can_advance = _step_targets(data)
        elif step == 4:
            can_advance = _step_tone(data)
        else:
            can_advance = _step_keys(data)

        st.markdown("---")
        col_back, col_spacer, col_next = st.columns([1, 2, 1])
        with col_back:
            if step > 1:
                if st.button("← Back", key=f"back_{step}"):
                    st.session_state["wizard_step"] = step - 1
                    st.rerun()
        with col_next:
            if step < 5:
                if st.button("Next →", key=f"next_{step}", disabled=not can_advance):
                    st.session_state["wizard_step"] = step + 1
                    st.rerun()
            else:
                if st.button("Finish setup", key="finish", type="primary", disabled=not can_advance):
                    try:
                        resume_ctx = _build_resume_context(data)
                        war_plan = _build_war_plan(data)
                        contact = _build_contact_info(data)
                        _write_config_local(war_plan, resume_ctx, contact)
                        _write_env(data)
                        st.success("✅ Setup complete! Reloading...")
                        for k in ("wizard_step", "wizard_data"):
                            st.session_state.pop(k, None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not write config: {e}")


def render_profile_form(values: dict) -> dict:
    """Flat (non-paged) form of the core wizard inputs. Used by Settings."""
    data = dict(_default_wizard_data())
    data.update(values or {})

    with st.form("profile_form"):
        st.markdown("### Profile")
        data["name"] = st.text_input("Full name", value=data.get("name", ""))
        data["email"] = st.text_input("Email", value=data.get("email", ""))
        data["phone"] = st.text_input("Phone", value=data.get("phone", ""))
        data["linkedin"] = st.text_input("LinkedIn URL", value=data.get("linkedin", ""))
        data["github"] = st.text_input("GitHub URL", value=data.get("github", ""))
        data["website"] = st.text_input("Portfolio / website URL", value=data.get("website", ""))

        st.markdown("### Resume")
        data["headline"] = st.text_input("Current role / headline", value=data.get("headline", ""))
        data["differentiators"] = st.text_area(
            "Differentiators (one per line)", value=data.get("differentiators", ""), height=200,
        )
        data["skills"] = st.text_input("Skills", value=data.get("skills", ""))
        data["education"] = st.text_input("Education", value=data.get("education", ""))

        st.markdown("### Targets")
        data["target_roles"] = st.multiselect(
            "Target role types",
            options=DEFAULT_ROLE_OPTIONS,
            default=data.get("target_roles", DEFAULT_ROLE_OPTIONS[:4]),
        )
        data["tier_1"] = st.text_area("Tier 1 companies", value=data.get("tier_1", ""), height=120)
        data["tier_2"] = st.text_area("Tier 2 companies", value=data.get("tier_2", ""), height=120)
        data["tier_3"] = st.text_area("Tier 3 companies", value=data.get("tier_3", ""), height=120)
        data["target_comp"] = st.text_input("Target compensation", value=data.get("target_comp", ""))
        data["remote_preference"] = st.checkbox(
            "Prefer remote", value=bool(data.get("remote_preference", True)),
        )

        st.markdown("### Tone & rules")
        tone_idx = TONE_OPTIONS.index(data["tone"]) if data.get("tone") in TONE_OPTIONS else 0
        data["tone"] = st.radio("Outreach tone", TONE_OPTIONS, index=tone_idx)
        data["hard_rules"] = st.text_area("Hard rules", value=data.get("hard_rules", ""), height=100)

        submitted = st.form_submit_button("Save profile")
        if submitted:
            st.session_state["_profile_form_submitted"] = True
    return data
