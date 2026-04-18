"""AI match scoring engine — scores each scouted role 1-10 against resume."""

from config import RESUME_CONTEXT, WAR_PLAN
from llm import GEMINI_FAST, gemini_json

SCORING_PROMPT = """You are an expert career match evaluator. Score how well this candidate matches the job.

CANDIDATE RESUME:
{resume}

JOB TO EVALUATE:
- Company: {company}
- Role: {role}
- Type: {role_type}
- Remote: {remote}
- Source snippet: {snippet}

SCORING RUBRIC:
1-3: Poor match — missing key skills, wrong seniority, wrong domain
4-6: Partial match — some skills align but gaps exist
7-8: Strong match — most skills align, seniority fits
9-10: Exceptional match — resume reads like it was written for this role

SCORING FACTORS (weighted):
- Role title match to target roles (HIGH): {target_roles}
- Skills overlap with resume (HIGH)
- Seniority fit: 1-5 years experience range (MEDIUM)
- Remote-friendly (MEDIUM)
- Company stage/prestige (LOW)

Return ONLY valid JSON:
{{
    "score": <1-10>,
    "reasoning": "<one sentence explaining the score>",
    "top_strengths": ["<strength 1>", "<strength 2>"],
    "gaps": ["<gap 1 or 'None identified'>"]
}}"""


def score_job(job: dict) -> dict:
    """Score a single job against the resume."""
    prompt = SCORING_PROMPT.format(
        resume=RESUME_CONTEXT,
        company=job.get("company", "Unknown"),
        role=job.get("role", "Unknown"),
        role_type=job.get("role_type", ""),
        remote=job.get("remote", ""),
        snippet=job.get("snippet", "No description available"),
        target_roles=", ".join(WAR_PLAN["target_roles"]),
    )

    try:
        result = gemini_json(prompt, model=GEMINI_FAST, max_tokens=400)
        return {
            "score": int(result.get("score", 5)),
            "reasoning": result.get("reasoning", ""),
            "top_strengths": result.get("top_strengths", []),
            "gaps": result.get("gaps", []),
        }
    except Exception as e:
        return {
            "score": None,
            "reasoning": f"Scoring unavailable: {e}",
            "top_strengths": [],
            "gaps": [],
        }


def score_jobs(jobs: list, progress_callback=None) -> list:
    """Score a list of jobs. Updates each job dict in place and returns it."""
    for i, job in enumerate(jobs):
        if job.get("score") is not None:
            continue
        result = score_job(job)
        job["score"] = result["score"]
        job["score_reasoning"] = result["reasoning"]
        job["score_strengths"] = result["top_strengths"]
        job["score_gaps"] = result["gaps"]
        if progress_callback:
            progress_callback(f"Scored {i+1}/{len(jobs)}: {job['company']} — {result['score']}/10", (i+1) / len(jobs))
    return jobs
