"""Local JSON-based application tracker."""

import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
APPS_FILE = DATA_DIR / "applications.json"
LOG_FILE = DATA_DIR / "daily_log.json"

STATUSES = [
    "to_apply", "applied", "referral_sent", "phone_screen",
    "technical", "final_round", "offer", "rejected", "skipped",
]


def _load(path: Path) -> list:
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _save(path: Path, data: list):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_applications() -> list:
    return _load(APPS_FILE)


def save_applications(apps: list):
    _save(APPS_FILE, apps)


def add_application(job: dict, status: str = "to_apply") -> dict:
    apps = load_applications()
    app = {
        "id": str(uuid.uuid4()),
        "company": job.get("company", ""),
        "role": job.get("role", ""),
        "tier": job.get("tier", 0),
        "role_type": job.get("role_type", ""),
        "remote": job.get("remote", ""),
        "url": job.get("url", ""),
        "status": status,
        "applied_date": datetime.now().strftime("%Y-%m-%d") if status == "applied" else "",
        "referral": False,
        "referral_contact": "",
        "salary_range": job.get("salary_range", ""),
        "notes": "",
        "outreach_generated": False,
        "cover_letter_generated": False,
        "follow_up_date": "",
        "score": job.get("score", 0),
        "score_reasoning": job.get("score_reasoning", ""),
        "source_job_id": job.get("id", ""),
    }
    if status == "applied":
        app["follow_up_date"] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    apps.append(app)
    save_applications(apps)
    log_activity("application_added", {
        "company": app["company"], "role": app["role"], "status": status,
    })
    return app


def update_status(app_id: str, new_status: str, **kwargs) -> dict | None:
    apps = load_applications()
    for app in apps:
        if app["id"] == app_id:
            app["status"] = new_status
            if new_status == "applied" and not app.get("applied_date"):
                app["applied_date"] = datetime.now().strftime("%Y-%m-%d")
                app["follow_up_date"] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            for k, v in kwargs.items():
                if k in app:
                    app[k] = v
            save_applications(apps)
            log_activity("status_updated", {
                "company": app["company"], "role": app["role"], "new_status": new_status,
            })
            try:
                from interview_prep import generate_prep, save_prep, get_prep, INTERVIEW_STAGES
                if new_status in INTERVIEW_STAGES:
                    existing = get_prep(app_id)
                    today = datetime.now().strftime("%Y-%m-%d")
                    if not (existing and existing.get("generated_date") == today):
                        prep = generate_prep(app)
                        save_prep(app_id, prep)
            except Exception as e:
                print(f"[tracker] interview prep generation failed: {e}", file=sys.stderr)
            return app
    return None


def update_application(app_id: str, **kwargs) -> dict | None:
    apps = load_applications()
    for app in apps:
        if app["id"] == app_id:
            for k, v in kwargs.items():
                app[k] = v
            save_applications(apps)
            return app
    return None


def get_application(app_id: str) -> dict | None:
    for app in load_applications():
        if app["id"] == app_id:
            return app
    return None


def get_stats() -> dict:
    apps = load_applications()
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())

    by_status = {}
    for s in STATUSES:
        by_status[s] = len([a for a in apps if a["status"] == s])

    applied_this_week = len([
        a for a in apps
        if a.get("applied_date")
        and datetime.strptime(a["applied_date"], "%Y-%m-%d").date() >= week_start
        and a["status"] not in ("skipped", "to_apply")
    ])

    applied_today = len([
        a for a in apps
        if a.get("applied_date")
        and a["applied_date"] == today.strftime("%Y-%m-%d")
        and a["status"] not in ("skipped", "to_apply")
    ])

    active_pipeline = len([
        a for a in apps
        if a["status"] in ("applied", "referral_sent", "phone_screen", "technical", "final_round")
    ])

    total_applied = len([
        a for a in apps if a["status"] not in ("to_apply", "skipped")
    ])

    return {
        "by_status": by_status,
        "applied_today": applied_today,
        "applied_this_week": applied_this_week,
        "active_pipeline": active_pipeline,
        "total_applied": total_applied,
        "total": len(apps),
    }


def get_due_followups() -> list:
    apps = load_applications()
    today = datetime.now().date()
    due = []
    for app in apps:
        if app["status"] in ("applied", "referral_sent") and app.get("follow_up_date"):
            fu_date = datetime.strptime(app["follow_up_date"], "%Y-%m-%d").date()
            days_overdue = (today - fu_date).days
            if days_overdue >= 0:
                app["days_overdue"] = days_overdue
                due.append(app)
    due.sort(key=lambda x: x["days_overdue"], reverse=True)
    return due


def get_upcoming_followups(days_ahead: int = 7) -> list:
    apps = load_applications()
    today = datetime.now().date()
    upcoming = []
    for app in apps:
        if app["status"] in ("applied", "referral_sent") and app.get("follow_up_date"):
            fu_date = datetime.strptime(app["follow_up_date"], "%Y-%m-%d").date()
            days_until = (fu_date - today).days
            if 0 < days_until <= days_ahead:
                app["days_until_followup"] = days_until
                upcoming.append(app)
    upcoming.sort(key=lambda x: x["days_until_followup"])
    return upcoming


def get_weekly_velocity() -> dict:
    apps = load_applications()
    today = datetime.now().date()
    weeks = {}
    for app in apps:
        if app.get("applied_date") and app["status"] not in ("to_apply", "skipped"):
            app_date = datetime.strptime(app["applied_date"], "%Y-%m-%d").date()
            week_num = (app_date - (today - timedelta(days=today.weekday()))).days // 7
            week_label = f"Week {abs(week_num)}" if week_num <= 0 else f"Week +{week_num}"
            iso_week = app_date.isocalendar()[1]
            weeks[iso_week] = weeks.get(iso_week, 0) + 1
    return weeks


def log_activity(action: str, details: dict):
    log = _load(LOG_FILE)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "action": action,
        "details": details,
    }
    log.append(entry)
    _save(LOG_FILE, log)


def get_daily_log(date: str | None = None) -> list:
    log = _load(LOG_FILE)
    target = date or datetime.now().strftime("%Y-%m-%d")
    return [e for e in log if e.get("date") == target]


def export_csv() -> str:
    import csv
    import io
    apps = load_applications()
    if not apps:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=apps[0].keys())
    writer.writeheader()
    writer.writerows(apps)
    return buf.getvalue()
