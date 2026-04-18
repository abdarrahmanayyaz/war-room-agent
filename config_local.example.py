"""Template — copy to `config_local.py` and edit.

`config_local.py` is gitignored. Anything defined here overrides the
defaults in `config.py`. You only need to define what you want to override.
"""

WAR_PLAN = {
    "target_roles": [
        "Forward Deployed Engineer",
        "AI Solutions Engineer",
        "Applied AI Engineer",
        "Developer Relations Engineer",
    ],
    "tier_1": ["Company A", "Company B"],
    "tier_2": ["Company C", "Company D"],
    "tier_3": ["Company E", "Company F"],
    "keywords": ["AI engineer", "LLM", "agentic", "solutions engineer"],
    "remote_preference": "remote-first",
    "wide_net": True,
    "target_comp": "$200K+",
    "weekly_target": 10,
    "min_experience_years": 0,
    "max_experience_years": 5,
    "start_date": "2026-04-01",
    "plan_days": 60,
}

RESUME_CONTEXT = """
Your Name — Current Role at Current Company

KEY DIFFERENTIATORS (use 1-2 most relevant per role):

1. Flagship project with metrics: e.g., "Shipped AI eval framework — 80% failure rate uncovered, 90% groundedness improvement, adopted org-wide."
2. Client-facing experience: e.g., "Primary technical partner for Fortune 500 engineering teams — perfect CSAT."
3. Founder story: e.g., "Built X — multi-model inference with graceful degradation."
4. Technical depth: e.g., "Full-stack AI app serving 1,000+ users with 40% improved response relevance."

SKILLS: Python, TypeScript, React, OpenAI/Claude APIs, LLM Evaluation, Prompt Engineering, ...

EDUCATION: B.S. Computer Science, University — GPA 3.7, honors

TONE: Warm, relationship-first. Conversational, not salesy. Lead with genuine interest in the company's mission.

DO NOT mention things you want to avoid in generated content (e.g., buzzwords you dislike).
""".strip()

CONTACT_INFO = {
    "name": "Your Name",
    "email": "you@example.com",
    "phone": "",
    "linkedin": "linkedin.com/in/your-handle",
    "github": "github.com/your-handle",
    "website": "your-site.com",
}
