"""War Room configuration.

Defaults shown here are generic examples. To personalize, copy
`config_local.example.py` to `config_local.py` and fill in your own
target roles / companies / resume / contact info. `config_local.py` is
gitignored and will override anything it defines.
"""

from datetime import date

WAR_PLAN = {
    "target_roles": [
        "Forward Deployed Engineer",
        "AI Solutions Engineer",
        "Applied AI Engineer",
        "Developer Relations Engineer",
        "Solutions Architect AI",
    ],
    "tier_1": ["Anthropic", "OpenAI", "Google DeepMind"],
    "tier_2": ["Vercel", "Datadog", "Cloudflare", "MongoDB", "Stripe"],
    "tier_3": ["GitLab", "Notion", "Linear", "Supabase", "Sourcegraph"],
    "keywords": [
        "AI engineer", "LLM", "agentic", "forward deployed",
        "solutions engineer", "developer advocate",
    ],
    "remote_preference": "remote-first",
    "wide_net": True,
    "target_comp": "",
    "weekly_target": 10,
    "min_experience_years": 0,
    "max_experience_years": 5,
    "start_date": date.today().isoformat(),
    "plan_days": 60,
}

RESUME_CONTEXT = """
<YOUR NAME> — <YOUR CURRENT ROLE>

KEY DIFFERENTIATORS (use these in outreach — pick the 1-2 most relevant per role):

1. <DIFFERENTIATOR 1 — what you shipped, with metrics>
2. <DIFFERENTIATOR 2 — flagship story, with outcome>
3. <DIFFERENTIATOR 3 — relevant experience, with numbers>
4. <DIFFERENTIATOR 4>
5. <DIFFERENTIATOR 5>

SKILLS: <comma-separated list — languages, frameworks, tools>

EDUCATION: <degree, school, honors>

TONE: <how your outreach should sound — warm/formal/technical/etc.>

DO NOT mention <anything you want to avoid in generated content>.
""".strip()

CONTACT_INFO = {
    "name": "<Your Name>",
    "email": "<you@example.com>",
    "phone": "",
    "linkedin": "",
    "github": "",
    "website": "",
}

try:
    from config_local import (  # type: ignore
        WAR_PLAN as _LOCAL_WAR_PLAN,
        RESUME_CONTEXT as _LOCAL_RESUME,
        CONTACT_INFO as _LOCAL_CONTACT,
    )
    WAR_PLAN = _LOCAL_WAR_PLAN
    RESUME_CONTEXT = _LOCAL_RESUME
    CONTACT_INFO = _LOCAL_CONTACT
except ImportError:
    pass
