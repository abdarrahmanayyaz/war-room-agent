"""AI outreach generator — cover letters, LinkedIn DMs, cold emails, resume bullets."""

import json
from pathlib import Path

from config import CONTACT_INFO, RESUME_CONTEXT
from llm import GEMINI_QUALITY, gemini_json

SYSTEM_PROMPT = """You are a career coach writing outreach for a job applicant.

CANDIDATE:
{resume}

RULES:
- Tone: Warm, relationship-first. Lead with genuine enthusiasm about the company's mission or product.
- Conversational, not salesy. Never desperate.
- DO NOT mention "RAG pipelines" anywhere — ever.
- Pick the 1-2 most relevant differentiators for THIS specific role.
- Role-type guidance:
  * FDE roles → emphasize: client-facing, shipped AI workspace at Oracle, Fortune 500 enterprise experience, Signl founder story
  * AI Solutions roles → emphasize: AI eval framework, LLM-as-judge, production AI systems
  * DevRel roles → emphasize: Signl (founder/builder), Genentech presentation, technical writing potential
  * Startup AI → emphasize: scrappiness, full-stack (Triage AI), founding experience (Signl)
- Contact info: {name}, {email}, {linkedin}"""


def generate_outreach(job: dict, has_referral: bool = False) -> dict:
    """Generate all outreach content for a job."""
    if has_referral:
        referral_context = "The candidate has a referral contact at this company. Write the LinkedIn DM as a warm referral ask to someone they already know or a mutual connection. Tone: friendly, brief, direct."
    else:
        referral_context = "The candidate has NO referral. Write cold outreach. Add a note at the end of the LinkedIn DM: 'Tip: Check LinkedIn for 2nd-degree connections before sending.'"

    system = SYSTEM_PROMPT.format(
        resume=RESUME_CONTEXT,
        name=CONTACT_INFO["name"],
        email=CONTACT_INFO["email"],
        linkedin=CONTACT_INFO["linkedin"],
    )

    user_prompt = f"""Generate outreach for this role:

Company: {job.get('company', 'Unknown')}
Role: {job.get('role', 'Unknown')}
Role Type: {job.get('role_type', 'AI Engineer')}
Remote: {job.get('remote', 'Unknown')}
Job URL: {job.get('url', '')}
Match Score: {job.get('score', 'N/A')}/10
Match Reasoning: {job.get('score_reasoning', 'N/A')}
Snippet: {job.get('snippet', 'No description available')}

{referral_context}

Return ONLY valid JSON:
{{
    "bullets": ["<3-4 tailored resume bullets mapping candidate to role>"],
    "cover_letter": "<5-6 paragraph cover letter. Start with 'Dear [Company] Hiring Team,'. End with candidate's name.>",
    "linkedin_dm": "<3-4 sentence LinkedIn message. Casual, warm.>",
    "cold_email": "<Subject: ...\\n\\n5-6 sentence email. Professional but warm.>",
    "who_to_contact": "<Suggest job TITLES to look for at this company, e.g. 'VP Engineering, Head of AI, Engineering Manager — someone on the team this role reports to'>"
}}"""

    try:
        return gemini_json(user_prompt, model=GEMINI_QUALITY, system=system, max_tokens=2500)
    except Exception as e:
        return {
            "bullets": [f"Error generating content: {e}"],
            "cover_letter": f"Error: {e}",
            "linkedin_dm": f"Error: {e}",
            "cold_email": f"Error: {e}",
            "who_to_contact": "VP Engineering, Head of AI, Engineering Manager",
        }


def save_outreach(job_id: str, outreach: dict):
    """Save generated outreach to outreach.json."""
    outreach_file = Path(__file__).parent / "data" / "outreach.json"
    data = []
    if outreach_file.exists():
        with open(outreach_file) as f:
            data = json.load(f)

    found = False
    for entry in data:
        if entry.get("job_id") == job_id:
            entry["outreach"] = outreach
            found = True
            break
    if not found:
        data.append({"job_id": job_id, "outreach": outreach})

    with open(outreach_file, "w") as f:
        json.dump(data, f, indent=2)


def get_outreach(job_id: str) -> dict | None:
    """Load saved outreach for a job."""
    outreach_file = Path(__file__).parent / "data" / "outreach.json"
    if not outreach_file.exists():
        return None
    with open(outreach_file) as f:
        data = json.load(f)
    for entry in data:
        if entry.get("job_id") == job_id:
            return entry.get("outreach")
    return None
