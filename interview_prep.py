"""Auto-generated interview prep packets for pipeline interview stages."""

import json
from datetime import datetime
from pathlib import Path

from config import RESUME_CONTEXT
from llm import GEMINI_QUALITY, gemini_json, perplexity_search

INTERVIEW_STAGES = ("phone_screen", "technical", "final_round")
PREP_FILE = Path(__file__).parent / "data" / "interview_prep.json"

_STAGE_FOCUS = {
    "phone_screen": (
        "Behavioral and culture fit — 'tell me about yourself', why this company, "
        "communication style, motivation, and high-level resume walkthrough."
    ),
    "technical": (
        "System design, coding approach, and technical depth on AI evaluation, "
        "LLM-powered systems, and agentic workflows."
    ),
    "final_round": (
        "Team fit, leadership signals, strategic thinking, negotiation prep, "
        "and sharp questions to ask leadership."
    ),
}


def _load_prep() -> list:
    if not PREP_FILE.exists():
        return []
    with open(PREP_FILE) as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _save_prep(data: list):
    with open(PREP_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def get_prep(app_id: str) -> dict | None:
    """Load saved prep for an application."""
    for item in _load_prep():
        if item.get("app_id") == app_id:
            return item
    return None


def save_prep(app_id: str, prep: dict):
    """Upsert a prep packet keyed by app_id."""
    data = _load_prep()
    entry = {
        "app_id": app_id,
        "generated_date": datetime.now().strftime("%Y-%m-%d"),
        "stage": prep.get("stage", ""),
        **prep,
    }
    found = False
    for i, item in enumerate(data):
        if item.get("app_id") == app_id:
            data[i] = entry
            found = True
            break
    if not found:
        data.append(entry)
    _save_prep(data)


def _fetch_company_research(company: str, role: str) -> dict:
    """Fetch company interview research via Perplexity. Never raises."""
    query = (
        f"Research {company} for a {role} interview. Focus on: what the company does, "
        f"recent news, the team this role would join, recent engineering/AI work they've "
        f"shipped, and common interview themes reported for {role} roles there. "
        "Return ONLY valid JSON matching this exact schema, no prose or markdown: "
        '{"company_brief": "<2-3 sentence summary: what they do, recent news, team this role is on>", '
        '"recent_technical_work": ["<engineering/AI achievement 1>", "<2>", "<3>"], '
        '"glassdoor_themes": ["<common interview theme 1>", "<2>", "<3>"]}'
    )
    try:
        result = perplexity_search(query, model="sonar", max_tokens=800)
        content = result.get("content") or {}
        if not isinstance(content, dict):
            return {"company_brief": "", "recent_technical_work": [], "glassdoor_themes": []}
        content.setdefault("company_brief", "")
        content.setdefault("recent_technical_work", [])
        content.setdefault("glassdoor_themes", [])
        return content
    except Exception:
        return {"company_brief": "", "recent_technical_work": [], "glassdoor_themes": []}


def generate_prep(application: dict) -> dict:
    """Generate a stage-specific interview prep packet."""
    stage = application.get("status", "")
    if stage not in INTERVIEW_STAGES:
        raise ValueError(f"Application status '{stage}' is not an interview stage")

    company = application.get("company", "")
    role = application.get("role", "")
    role_type = application.get("role_type", "")
    focus = _STAGE_FOCUS[stage]

    research = _fetch_company_research(company, role)

    prompt = f"""Generate an interview prep packet for this application.

CANDIDATE:
{RESUME_CONTEXT}

APPLICATION:
- Company: {company}
- Role: {role}
- Role type: {role_type}
- Interview stage: {stage}

STAGE-SPECIFIC FOCUS:
{focus}

COMPANY RESEARCH (from Perplexity — may be empty):
- Brief: {research.get('company_brief', '')}
- Recent technical work: {research.get('recent_technical_work', [])}
- Common interview themes: {research.get('glassdoor_themes', [])}

INSTRUCTIONS:
- Tailor questions, stories, and topics to the role, company, and interview stage.
- STAR stories should pull from the candidate's strongest differentiators (AI eval framework, Oracle AI workspace, Signl, Fortune 500 client work).
- Keep every field tight — no fluff, no generic advice.
- DO NOT mention "RAG pipelines".

Return ONLY valid JSON:
{{
    "company_brief": "<use the perplexity brief if available, otherwise synthesize one>",
    "likely_questions": ["<5-7 questions tailored to this role and stage>"],
    "star_stories_to_use": [
        {{
            "question_type": "<e.g., 'Client-facing challenge'>",
            "story": "<name + one-line>",
            "key_metrics": "<numbers to cite>"
        }}
    ],
    "system_design_topics": ["<2-3 topics relevant to this role>"],
    "questions_to_ask_them": ["<4-5 smart questions>"],
    "role_specific_tips": "<stage-specific advice paragraph>"
}}"""

    today = datetime.now().strftime("%Y-%m-%d")

    try:
        result = gemini_json(prompt, model=GEMINI_QUALITY, max_tokens=2500)
    except Exception as e:
        result = {
            "company_brief": research.get("company_brief", ""),
            "likely_questions": [],
            "star_stories_to_use": [],
            "system_design_topics": [],
            "questions_to_ask_them": [],
            "role_specific_tips": f"Error generating prep: {e}",
        }

    result["stage"] = stage
    result["generated_date"] = today
    result["company"] = company
    result["role"] = role
    return result
