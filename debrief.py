"""Daily summary + tomorrow's priorities generator."""

import json
from datetime import datetime, timedelta

from config import WAR_PLAN
from llm import GEMINI_FAST, gemini_json


def generate_debrief(daily_log: list, tracker_data: list, config: dict = WAR_PLAN) -> dict:
    """Generate AI-powered daily debrief with summary and priorities."""
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())

    applied_today = len([
        a for a in tracker_data
        if a.get("applied_date") == today.strftime("%Y-%m-%d")
        and a["status"] not in ("to_apply", "skipped")
    ])
    applied_this_week = len([
        a for a in tracker_data
        if a.get("applied_date")
        and datetime.strptime(a["applied_date"], "%Y-%m-%d").date() >= week_start
        and a["status"] not in ("to_apply", "skipped")
    ])

    roles_scouted = len([e for e in daily_log if e.get("action") == "scout_completed"])
    new_roles_found = sum(
        e.get("details", {}).get("new_roles", 0)
        for e in daily_log if e.get("action") == "scout_completed"
    )
    outreach_generated = len([e for e in daily_log if e.get("action") == "outreach_generated"])
    followups_sent = len([e for e in daily_log if e.get("action") == "followup_sent"])

    overdue = []
    upcoming_interviews = []
    for app in tracker_data:
        if app["status"] in ("applied", "referral_sent") and app.get("follow_up_date"):
            fu_date = datetime.strptime(app["follow_up_date"], "%Y-%m-%d").date()
            if fu_date <= today:
                days_over = (today - fu_date).days
                overdue.append({"company": app["company"], "role": app["role"], "days_overdue": days_over})
        if app["status"] in ("phone_screen", "technical", "final_round"):
            upcoming_interviews.append({"company": app["company"], "role": app["role"], "status": app["status"]})

    week_data = {}
    for app in tracker_data:
        if app.get("applied_date") and app["status"] not in ("to_apply", "skipped"):
            app_date = datetime.strptime(app["applied_date"], "%Y-%m-%d").date()
            iso_week = app_date.isocalendar()[1]
            week_data[iso_week] = week_data.get(iso_week, 0) + 1

    today_summary = {
        "roles_scouted": new_roles_found,
        "outreach_generated": outreach_generated,
        "applications_logged": applied_today,
        "followups_sent": followups_sent,
        "week_progress": f"{applied_this_week}/{config['weekly_target']}",
    }

    priorities_context = f"""
Today's stats: {applied_today} apps sent, {applied_this_week}/{config['weekly_target']} for the week, {new_roles_found} new roles scouted.
Overdue follow-ups: {json.dumps(overdue[:5])}
Upcoming interviews: {json.dumps(upcoming_interviews[:5])}
Weekly target gap: {max(0, config['weekly_target'] - applied_this_week)} more apps needed this week.
Total active pipeline: {len([a for a in tracker_data if a['status'] in ('applied', 'referral_sent', 'phone_screen', 'technical', 'final_round')])}
"""

    prompt = f"""Based on this job search pipeline state, generate 3-5 prioritized action items for tomorrow.

{priorities_context}

Return ONLY valid JSON:
{{
    "priorities": [
        {{"urgency": "high|medium|low", "action": "<specific action item>"}}
    ],
    "motivation": "<one sharp motivational line — blunt, competitive, no fluff>"
}}"""

    try:
        ai_result = gemini_json(prompt, model=GEMINI_FAST, max_tokens=700)
    except Exception:
        ai_result = {
            "priorities": [
                {"urgency": "medium", "action": f"Apply to {max(0, config['weekly_target'] - applied_this_week)} more roles to hit weekly target"},
            ],
            "motivation": "Every app an ex-Oracle engineer doesn't send is your advantage.",
        }

    return {
        "today_summary": today_summary,
        "tomorrow_priorities": ai_result.get("priorities", []),
        "week_over_week": week_data,
        "motivation": ai_result.get("motivation", "Keep pushing."),
        "generated_at": datetime.now().isoformat(),
    }
