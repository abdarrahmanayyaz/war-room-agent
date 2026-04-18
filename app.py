"""WAR ROOM — Daily Job Application Agent. Streamlit main app."""

import json
import os
from datetime import datetime, timedelta

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page Config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="WAR ROOM",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from onboarding import (
    needs_onboarding,
    render_wizard,
    render_profile_form,
    _write_config_local,
    _upsert_env,
    _test_gemini,
    _test_perplexity,
    _build_resume_context,
    _build_war_plan,
    _build_contact_info,
)

if needs_onboarding():
    render_wizard()
    st.stop()

from config import WAR_PLAN, RESUME_CONTEXT, CONTACT_INFO

# ── Dark War Room Theme ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&family=Inter:wght@400;500;600;700&display=swap');

/* Dark background */
.stApp { background-color: #0a0a0a; }
section[data-testid="stSidebar"] { background-color: #111; }

/* War Room Header */
.war-header {
    font-family: 'JetBrains Mono', monospace;
    color: #ff2a1f;
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin: 0; padding: 0.5rem 0 0 0;
}
.day-counter {
    font-family: 'JetBrains Mono', monospace;
    color: #666;
    font-size: 1rem;
    letter-spacing: 0.1em;
    margin-top: -0.5rem;
}

/* Stat pills */
.stat-row { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; }
.stat-pill {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 0.6rem 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    color: #ccc;
    font-size: 0.85rem;
}
.stat-pill .num {
    color: #ff2a1f;
    font-weight: 700;
    font-size: 1.1rem;
}
.stat-pill .label { color: #888; font-size: 0.75rem; }

/* Job cards */
.job-card {
    background: #141414;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.2s;
}
.job-card:hover { border-color: #ff2a1f44; }

.company-name {
    font-family: 'Inter', sans-serif;
    color: #eee;
    font-size: 1.15rem;
    font-weight: 700;
    margin: 0;
}
.role-title {
    font-family: 'JetBrains Mono', monospace;
    color: #888;
    font-size: 0.85rem;
    margin: 0.2rem 0 0.6rem 0;
}

/* Score rings */
.score-ring {
    width: 48px; height: 48px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 800;
    font-size: 1.1rem;
    flex-shrink: 0;
}
.score-high { border: 3px solid #22c55e; color: #22c55e; }
.score-mid { border: 3px solid #eab308; color: #eab308; }
.score-low { border: 3px solid #555; color: #555; }

/* Badges */
.badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    margin-right: 0.4rem;
}
.badge-t1 { background: #ff2a1f22; color: #ff2a1f; border: 1px solid #ff2a1f44; }
.badge-t2 { background: #eab30822; color: #eab308; border: 1px solid #eab30844; }
.badge-t3 { background: #3b82f622; color: #3b82f6; border: 1px solid #3b82f644; }
.badge-new { background: #22c55e22; color: #22c55e; border: 1px solid #22c55e44; }
.badge-remote { background: #8b5cf622; color: #8b5cf6; border: 1px solid #8b5cf644; }
.badge-hybrid { background: #f9731622; color: #f97316; border: 1px solid #f9731644; }
.badge-role { background: #06b6d422; color: #06b6d4; border: 1px solid #06b6d444; }
.badge-direct { background: #22c55e22; color: #22c55e; border: 1px solid #22c55e44; }
.badge-perplexity { background: #88888822; color: #888; border: 1px solid #88888844; }

/* Referral check box */
.referral-check {
    background: #eab30811;
    border: 1px solid #eab30844;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.6rem 0;
    font-family: 'Inter', sans-serif;
    color: #eab308;
    font-size: 0.85rem;
}

/* Follow-up cards */
.followup-card {
    background: #141414;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}
.followup-overdue { border-left: 4px solid #ff2a1f; }
.followup-due-today { border-left: 4px solid #eab308; }
.followup-upcoming { border-left: 4px solid #22c55e; }

/* Kanban columns */
.kanban-col {
    background: #111;
    border-radius: 8px;
    padding: 0.8rem;
    min-height: 200px;
}
.kanban-header {
    font-family: 'JetBrains Mono', monospace;
    color: #888;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid #2a2a2a;
    margin-bottom: 0.6rem;
}
.kanban-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 0.6rem;
    margin-bottom: 0.5rem;
    font-size: 0.8rem;
}

/* Debrief sections */
.priority-box {
    background: #1e3a5f22;
    border: 1px solid #3b82f644;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.8rem 0;
}

/* Progress bar */
.progress-container {
    background: #1a1a1a;
    border-radius: 8px;
    height: 8px;
    width: 100%;
    margin: 0.5rem 0 1rem 0;
}
.progress-bar {
    height: 8px;
    border-radius: 8px;
    transition: width 0.3s;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] { gap: 0; }
.stTabs [data-baseweb="tab"] {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.05em;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* Copy button area */
.copy-area {
    background: #0d0d0d;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #aaa;
    white-space: pre-wrap;
    max-height: 300px;
    overflow-y: auto;
}

/* Motivation text */
.motivation {
    font-family: 'JetBrains Mono', monospace;
    color: #ff2a1f;
    font-size: 0.85rem;
    font-style: italic;
    padding: 1rem;
    border-left: 3px solid #ff2a1f;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ──────────────────────────────────────────────────

def _day_of_plan() -> int:
    start = datetime.strptime(WAR_PLAN["start_date"], "%Y-%m-%d").date()
    return (datetime.now().date() - start).days + 1


def _score_class(score: int | None) -> str:
    if score is None:
        return "score-low"
    if score >= 8:
        return "score-high"
    if score >= 5:
        return "score-mid"
    return "score-low"


def _tier_badge(tier: int) -> str:
    if tier == 1:
        return '<span class="badge badge-t1">T1</span>'
    if tier == 2:
        return '<span class="badge badge-t2">T2</span>'
    if tier == 3:
        return '<span class="badge badge-t3">T3</span>'
    return '<span class="badge badge-new">NEW</span>'


def _remote_badge(remote: str) -> str:
    if remote == "Full":
        return '<span class="badge badge-remote">REMOTE</span>'
    if remote == "Hybrid":
        return '<span class="badge badge-hybrid">HYBRID</span>'
    return '<span class="badge badge-hybrid">ON-SITE</span>'


def _load_settings() -> dict:
    settings_file = os.path.join(os.path.dirname(__file__), "data", "settings.json")
    defaults = {
        "wide_net": WAR_PLAN["wide_net"],
        "auto_scout": False,
        "match_scoring": True,
        "referral_check": True,
        "auto_followups": True,
        "remote_preference": True,
        "weekly_target": WAR_PLAN["weekly_target"],
        "experience_filter": True,
        "auto_generate_outreach_8plus": True,
        "tone": "Warm, relationship-first",
        "hard_rules": "",
        "start_date": WAR_PLAN.get("start_date"),
        "plan_days": WAR_PLAN.get("plan_days", 60),
    }
    if os.path.exists(settings_file):
        with open(settings_file) as f:
            saved = json.load(f)
        defaults.update(saved)
    return defaults


def _save_settings(settings: dict):
    settings_file = os.path.join(os.path.dirname(__file__), "data", "settings.json")
    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)


# ── API Key Check ─────────────────────────────────────────────────────

_has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
_has_perplexity = bool(os.environ.get("PERPLEXITY_API_KEY"))
_missing = []
if not _has_gemini:
    _missing.append("GEMINI_API_KEY (scoring, outreach, follow-ups, debrief)")
if not _has_perplexity:
    _missing.append("PERPLEXITY_API_KEY (job scouting)")
if _missing:
    st.warning(
        "**Missing API keys:** " + ", ".join(_missing) +
        ".\n\nAdd them to a `.env` file in the project root:\n\n"
        "```\nGEMINI_API_KEY=AIza...\nPERPLEXITY_API_KEY=pplx-...\n```"
    )


# ── Load Data ─────────────────────────────────────────────────────────

from tracker import (
    load_applications, save_applications, add_application, update_status,
    update_application, get_stats, get_due_followups, get_upcoming_followups,
    get_daily_log, log_activity, export_csv,
)
from scout import load_scouted, save_scouted, update_scouted_job, run_scout
from scorer import score_jobs
from tailor import generate_outreach, save_outreach, get_outreach
from interview_prep import generate_prep, save_prep, get_prep, INTERVIEW_STAGES

settings = _load_settings()
stats = get_stats()


# ── Header ────────────────────────────────────────────────────────────

day = _day_of_plan()
day_display = min(day, WAR_PLAN["plan_days"])

st.markdown(f'<p class="war-header">WAR ROOM</p>', unsafe_allow_html=True)
st.markdown(f'<p class="day-counter">DAY {day_display} OF {WAR_PLAN["plan_days"]}</p>', unsafe_allow_html=True)

# Stats row
due_followups = get_due_followups()
week_pct = min(100, int((stats["applied_this_week"] / settings["weekly_target"]) * 100)) if settings["weekly_target"] > 0 else 0
bar_color = "#22c55e" if week_pct >= 100 else ("#eab308" if week_pct >= 50 else "#ff2a1f")

st.markdown(f"""
<div class="stat-row">
    <div class="stat-pill"><span class="label">TODAY</span> <span class="num">{stats["applied_today"]}</span></div>
    <div class="stat-pill"><span class="label">THIS WEEK</span> <span class="num">{stats["applied_this_week"]}/{settings["weekly_target"]}</span></div>
    <div class="stat-pill"><span class="label">TOTAL</span> <span class="num">{stats["total_applied"]}</span></div>
    <div class="stat-pill"><span class="label">PIPELINE</span> <span class="num">{stats["active_pipeline"]}</span></div>
    <div class="stat-pill"><span class="label">FOLLOW-UPS DUE</span> <span class="num">{len(due_followups)}</span></div>
</div>
<div class="progress-container">
    <div class="progress-bar" style="width: {week_pct}%; background: {bar_color};"></div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────

tab_scout, tab_followups, tab_tracker, tab_debrief, tab_settings = st.tabs([
    "SCOUT", "FOLLOW-UPS", "TRACKER", "DEBRIEF", "SETTINGS",
])


# ═══════════════════════════════════════════════════════════════════════
# TAB 1: SCOUT
# ═══════════════════════════════════════════════════════════════════════
with tab_scout:
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        search_query = st.text_input("Search roles", placeholder="e.g., AI solutions engineer remote", label_visibility="collapsed")
    with col_btn:
        scout_clicked = st.button("Scout", type="primary", use_container_width=True)

    # Filters
    filter_cols = st.columns(6)
    with filter_cols[0]:
        f_all = st.button("All", use_container_width=True, key="f_all")
    with filter_cols[1]:
        f_named = st.button("Named Targets", use_container_width=True, key="f_named")
    with filter_cols[2]:
        f_new = st.button("New Discoveries", use_container_width=True, key="f_new")
    with filter_cols[3]:
        f_remote = st.button("Remote Only", use_container_width=True, key="f_remote")
    with filter_cols[4]:
        f_score7 = st.button("Score 7+", use_container_width=True, key="f_score7")
    with filter_cols[5]:
        f_unscored = st.button("Unscored", use_container_width=True, key="f_unscored")

    if "scout_filter" not in st.session_state:
        st.session_state.scout_filter = "all"

    if f_all:
        st.session_state.scout_filter = "all"
    elif f_named:
        st.session_state.scout_filter = "named"
    elif f_new:
        st.session_state.scout_filter = "new"
    elif f_remote:
        st.session_state.scout_filter = "remote"
    elif f_score7:
        st.session_state.scout_filter = "score7"
    elif f_unscored:
        st.session_state.scout_filter = "unscored"

    # Run scout — auto-chained scoring + outreach pre-generation
    if scout_clicked:
        progress_bar = st.progress(0)
        status_text = st.empty()

        def scout_progress(msg, pct):
            progress_bar.progress(min(pct, 1.0))
            status_text.text(f"Scouting... {msg}")

        new_jobs = run_scout(wide_net=settings["wide_net"], progress_callback=scout_progress)

        # Phase 2 — auto-score every new job (never leave unscored in UI)
        if new_jobs:
            score_bar = st.progress(0)

            def score_progress(msg, pct):
                score_bar.progress(min(pct, 1.0))
                status_text.text(f"Scoring {len(new_jobs)} roles... {msg}")

            score_jobs(new_jobs, progress_callback=score_progress)

            # Persist scores back into scouted.json
            scouted = load_scouted()
            for nj in new_jobs:
                for sj in scouted:
                    if sj["id"] == nj["id"]:
                        sj.update({
                            "score": nj.get("score"),
                            "score_reasoning": nj.get("score_reasoning"),
                            "score_strengths": nj.get("score_strengths"),
                            "score_gaps": nj.get("score_gaps"),
                        })
            save_scouted(scouted)
            score_bar.empty()

            # Phase 3 — pre-generate outreach for 8+ scored jobs
            high_match = [j for j in new_jobs if (j.get("score") or 0) >= 8 and not get_outreach(j["id"])]
            if high_match:
                out_bar = st.progress(0)
                total_hm = len(high_match)
                status_text.text(f"Pre-generating outreach for {total_hm} high-match roles...")
                for idx, job in enumerate(high_match):
                    try:
                        outreach = generate_outreach(job, has_referral=False)
                        save_outreach(job["id"], outreach)
                        log_activity("outreach_generated", {
                            "job_id": job["id"],
                            "company": job.get("company", ""),
                            "auto": True,
                        })
                    except Exception:
                        pass
                    out_bar.progress((idx + 1) / total_hm)
                out_bar.empty()

        progress_bar.empty()
        status_text.empty()
        st.toast(f"Found {len(new_jobs)} new roles")

    # Display scouted jobs
    scouted_jobs = load_scouted()

    active_filter = st.session_state.scout_filter
    if active_filter == "named":
        scouted_jobs = [j for j in scouted_jobs if j.get("discovery") == "named"]
    elif active_filter == "new":
        scouted_jobs = [j for j in scouted_jobs if j.get("tier", 0) == 0]
    elif active_filter == "remote":
        scouted_jobs = [j for j in scouted_jobs if j.get("remote") == "Full"]
    elif active_filter == "score7":
        scouted_jobs = [j for j in scouted_jobs if (j.get("score") or 0) >= 7]
    elif active_filter == "unscored":
        scouted_jobs = [j for j in scouted_jobs if j.get("score") is None]

    if search_query:
        sq = search_query.lower()
        scouted_jobs = [j for j in scouted_jobs if sq in j.get("company", "").lower() or sq in j.get("role", "").lower() or sq in j.get("snippet", "").lower()]

    scouted_jobs.sort(key=lambda j: (-(j.get("score") or 0), j["tier"] if j["tier"] > 0 else 4))

    # Hide processed cards — only show new/unstatused
    _processed = ("applied", "skipped", "saved", "referral_sent")
    scouted_jobs = [j for j in scouted_jobs if j.get("status", "new") not in _processed]

    # Batch mode — Process all 7+ roles without saved outreach
    batch_targets = [
        j for j in scouted_jobs
        if (j.get("score") or 0) >= 7 and not get_outreach(j["id"])
    ]
    batch_label = f"Process all 7+ roles ({len(batch_targets)})" if batch_targets else "Process all 7+ roles"
    if st.button(batch_label, disabled=not batch_targets, key="batch_7plus"):
        bar = st.progress(0)
        status = st.empty()
        total_b = len(batch_targets)
        count = 0
        for idx, job in enumerate(batch_targets):
            status.text(f"Generating outreach {idx+1}/{total_b} — {job.get('company', '')}")
            try:
                outreach = generate_outreach(job, has_referral=False)
                save_outreach(job["id"], outreach)
                log_activity("outreach_generated", {
                    "job_id": job["id"],
                    "company": job.get("company", ""),
                    "auto": True,
                })
                count += 1
            except Exception:
                pass
            bar.progress((idx + 1) / total_b)
        bar.empty()
        status.empty()
        st.toast(f"Generated outreach for {count} roles ✓")

    if not scouted_jobs:
        st.markdown("*No scouted jobs yet. Hit **Scout** to find roles.*")
    else:
        st.markdown(f"**{len(scouted_jobs)} roles** matching filter: `{active_filter}`")

    for job in scouted_jobs:
        score = job.get("score")
        score_cls = _score_class(score)
        score_display = str(score) if score is not None else "?"
        tier_html = _tier_badge(job.get("tier", 0))
        remote_html = _remote_badge(job.get("remote", ""))
        role_type_html = f'<span class="badge badge-role">{job.get("role_type", "AI")}</span>'
        if job.get("source") == "direct_api":
            source_html = '<span class="badge badge-direct">DIRECT</span>'
        else:
            source_html = '<span class="badge badge-perplexity">PERPLEXITY</span>'
        discovery_label = {"named": "TARGETED", "broad_sweep": "BROAD", "aggregator": "BOARD"}.get(job.get("discovery", ""), "")
        reasoning = job.get("score_reasoning") or ""

        st.markdown(f"""
        <div class="job-card" style="display: flex; gap: 1rem; align-items: flex-start;">
            <div class="score-ring {score_cls}">{score_display}</div>
            <div style="flex: 1;">
                <p class="company-name">{job.get('company', 'Unknown')}</p>
                <p class="role-title">{job.get('role', 'Unknown Role')}</p>
                <div>{tier_html}{remote_html}{role_type_html}{source_html}</div>
                {"<p style='color: #aaa; font-size: 0.8rem; margin-top: 0.4rem; font-family: Inter, sans-serif;'>" + reasoning + "</p>" if reasoning else ""}
                <p style="color: #555; font-size: 0.7rem; margin-top: 0.3rem;">{job.get('source', '')} &middot; {job.get('scouted_date', '')} &middot; {discovery_label}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        job_key = job["id"]

        # Quick Apply + View row
        qa_col, view_col = st.columns([2, 1])
        with qa_col:
            if st.button("⚡ Quick Apply", key=f"qa_{job_key}", use_container_width=True):
                existing = get_outreach(job["id"])
                if not existing:
                    with st.spinner("Generating outreach..."):
                        try:
                            existing = generate_outreach(job, has_referral=False)
                            save_outreach(job["id"], existing)
                            log_activity("outreach_generated", {
                                "job_id": job["id"],
                                "company": job.get("company", ""),
                                "auto": True,
                            })
                        except Exception as e:
                            st.error(f"Outreach generation failed: {e}")
                            existing = None

                dm_text = (existing or {}).get("linkedin_dm", "") if existing else ""
                if dm_text:
                    safe = json.dumps(dm_text)
                    st.components.v1.html(
                        f"""<script>navigator.clipboard && navigator.clipboard.writeText({safe});</script>""",
                        height=0,
                    )
                    with st.expander("LinkedIn DM (copied)", expanded=False):
                        st.code(dm_text, language=None)

                add_application(job, status="applied")
                update_scouted_job(job["id"], status="applied")
                st.toast(f"Applied to {job.get('company', '')} — {job.get('role', '')} ✓")
        with view_col:
            if job.get("url"):
                st.link_button("Open posting", job["url"], use_container_width=True)

        # Inline status buttons
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            if st.button("✅ Applied", key=f"apply_{job_key}", use_container_width=True):
                add_application(job, status="applied")
                update_scouted_job(job["id"], status="applied")
                st.toast(f"Applied to {job.get('company', '')} ✓")
        with s2:
            if st.button("🤝 Referral Sent", key=f"ref_{job_key}", use_container_width=True):
                add_application(job, status="referral_sent")
                update_scouted_job(job["id"], status="referral_sent")
                st.toast(f"Referral logged for {job.get('company', '')} ✓")
        with s3:
            if st.button("💾 Save", key=f"save_{job_key}", use_container_width=True):
                update_scouted_job(job["id"], status="saved")
                st.toast("Saved ✓")
        with s4:
            if st.button("⏭️ Skip", key=f"skip_{job_key}", use_container_width=True):
                update_scouted_job(job["id"], status="skipped")
                st.toast("Skipped ✓")

        # Inline outreach display if already generated
        existing_outreach = get_outreach(job["id"])
        if existing_outreach:
            with st.expander("Outreach Drafts"):
                st.markdown("**Tailored Resume Bullets**")
                for b in existing_outreach.get("bullets", []):
                    st.markdown(f"- {b}")

                st.markdown("**LinkedIn DM**")
                st.code(existing_outreach.get("linkedin_dm", ""), language=None)

                st.markdown("**Cold Email**")
                st.code(existing_outreach.get("cold_email", ""), language=None)

                st.markdown("**Cover Letter**")
                with st.expander("Show full cover letter"):
                    st.text(existing_outreach.get("cover_letter", ""))

                st.markdown(f"**Who to contact:** {existing_outreach.get('who_to_contact', '')}")

        st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════
# TAB 2: FOLLOW-UPS
# ═══════════════════════════════════════════════════════════════════════
with tab_followups:
    # Auto-generate follow-ups for stale applications if enabled
    if settings.get("auto_followups") and _has_gemini:
        from followup import auto_generate_followups
        all_apps = load_applications()
        auto_generated = auto_generate_followups(all_apps)
        if auto_generated:
            st.success(f"Auto-generated {len(auto_generated)} follow-up message(s).")

    st.markdown("### Action Required")

    due = get_due_followups()

    if not due:
        st.info("No follow-ups due. Keep applying!")
    else:
        for app in due:
            days = app.get("days_overdue", 0)
            border_class = "followup-overdue" if days > 0 else "followup-due-today"
            urgency = f"{days} DAYS OVERDUE" if days > 0 else "DUE TODAY"
            urgency_color = "#ff2a1f" if days > 0 else "#eab308"

            st.markdown(f"""
            <div class="followup-card {border_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #eee; font-weight: 700; font-family: Inter, sans-serif;">{app['company']}</span>
                        <span style="color: #888; font-family: JetBrains Mono, monospace; font-size: 0.8rem; margin-left: 0.5rem;">{app['role']}</span>
                    </div>
                    <span style="color: {urgency_color}; font-family: JetBrains Mono, monospace; font-size: 0.7rem; font-weight: 700;">{urgency}</span>
                </div>
                <p style="color: #666; font-size: 0.75rem; margin-top: 0.3rem;">Applied: {app.get('applied_date', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

            fkey = app["id"]
            col1, col2, col3, col4 = st.columns(4)

            # Check for existing follow-up
            from followup import get_followup, generate_followup, save_followup
            existing_fu = get_followup(app["id"])

            with col1:
                if st.button("Generate Follow-up", key=f"gen_fu_{fkey}"):
                    applied_date = datetime.strptime(app["applied_date"], "%Y-%m-%d").date()
                    days_since = (datetime.now().date() - applied_date).days
                    with st.spinner("Generating follow-up..."):
                        fu = generate_followup(app, days_since)
                        save_followup(app["id"], fu)
                        log_activity("followup_generated", {"company": app["company"]})
                    st.session_state[f"fu_data_{fkey}"] = fu
                    st.rerun()

            with col2:
                if st.button("Mark Followed Up", key=f"mark_fu_{fkey}"):
                    new_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                    update_application(app["id"], follow_up_date=new_date)
                    log_activity("followup_sent", {"company": app["company"]})
                    st.success("Marked! Next follow-up in 7 days.")
                    st.rerun()

            with col3:
                if st.button("No Response", key=f"noresp_{fkey}"):
                    update_status(app["id"], "rejected", notes="No response after follow-up")
                    st.rerun()

            with col4:
                if app.get("url"):
                    st.link_button("View Job", app["url"], key=f"fu_link_{fkey}")

            # Show follow-up content
            fu_data = st.session_state.get(f"fu_data_{fkey}") or existing_fu
            if fu_data:
                with st.expander("Follow-up Messages", expanded=True):
                    st.markdown("**Follow-up Email**")
                    st.code(fu_data.get("followup_email", ""), language=None)
                    st.markdown("**Follow-up LinkedIn**")
                    st.code(fu_data.get("followup_linkedin", ""), language=None)
                    action = fu_data.get("suggested_action", "follow_up")
                    action_colors = {"follow_up": "#22c55e", "try_different_contact": "#eab308", "move_on": "#ff2a1f"}
                    st.markdown(f"**Suggested:** <span style='color: {action_colors.get(action, '#888')}'>{action.replace('_', ' ').title()}</span>", unsafe_allow_html=True)

    # Upcoming follow-ups
    st.markdown("### Upcoming Follow-ups")
    upcoming = get_upcoming_followups()
    if not upcoming:
        st.markdown("*No upcoming follow-ups in the next 7 days.*")
    else:
        for app in upcoming:
            days_until = app.get("days_until_followup", 0)
            st.markdown(f"""
            <div class="followup-card followup-upcoming">
                <span style="color: #eee; font-weight: 600;">{app['company']}</span>
                <span style="color: #888; font-size: 0.8rem; margin-left: 0.5rem;">{app['role']}</span>
                <span style="color: #22c55e; font-size: 0.75rem; float: right;">in {days_until} day{'s' if days_until != 1 else ''}</span>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 3: TRACKER
# ═══════════════════════════════════════════════════════════════════════
with tab_tracker:
    st.markdown("### Pipeline")

    apps = load_applications()
    pipeline_statuses = ["to_apply", "applied", "referral_sent", "phone_screen", "technical", "final_round", "offer", "rejected"]
    status_labels = {
        "to_apply": "TO APPLY",
        "applied": "APPLIED",
        "referral_sent": "REFERRAL",
        "phone_screen": "PHONE SCREEN",
        "technical": "TECHNICAL",
        "final_round": "FINAL ROUND",
        "offer": "OFFER",
        "rejected": "REJECTED",
    }

    # Kanban board
    cols = st.columns(len(pipeline_statuses))
    for i, status_key in enumerate(pipeline_statuses):
        with cols[i]:
            status_apps = [a for a in apps if a["status"] == status_key]
            st.markdown(f"""
            <div class="kanban-header">{status_labels[status_key]} ({len(status_apps)})</div>
            """, unsafe_allow_html=True)

            for app in status_apps:
                score = app.get("score", 0) or 0
                score_cls = _score_class(score) if score else "score-low"

                # Follow-up urgency color
                border_color = "#2a2a2a"
                if app.get("follow_up_date") and app["status"] in ("applied", "referral_sent"):
                    fu_date = datetime.strptime(app["follow_up_date"], "%Y-%m-%d").date()
                    diff = (fu_date - datetime.now().date()).days
                    if diff < 0:
                        border_color = "#ff2a1f"
                    elif diff <= 2:
                        border_color = "#eab308"
                    else:
                        border_color = "#22c55e"

                st.markdown(f"""
                <div class="kanban-card" style="border-left: 3px solid {border_color};">
                    <div style="color: #ddd; font-weight: 600; font-size: 0.8rem;">{app['company']}</div>
                    <div style="color: #888; font-size: 0.7rem;">{app['role'][:25]}</div>
                    <div style="color: #555; font-size: 0.65rem; margin-top: 0.3rem;">
                        {app.get('applied_date', '') or ''} &middot; Score: {score or '?'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Expandable detail section
    st.markdown("### Application Details")
    if not apps:
        st.markdown("*No applications yet. Scout for roles and start applying!*")
    else:
        for app in sorted(apps, key=lambda a: a.get("applied_date", ""), reverse=True):
            with st.expander(f"{app['company']} — {app['role']} [{app['status'].upper()}]"):
                detail_cols = st.columns([2, 1])
                with detail_cols[0]:
                    new_status = st.selectbox(
                        "Status",
                        pipeline_statuses,
                        index=pipeline_statuses.index(app["status"]) if app["status"] in pipeline_statuses else 0,
                        key=f"status_{app['id'][:8]}",
                    )
                    notes = st.text_area("Notes", value=app.get("notes", ""), key=f"notes_{app['id'][:8]}")
                    if st.button("Update", key=f"update_{app['id'][:8]}"):
                        update_status(app["id"], new_status, notes=notes)
                        st.success("Updated!")
                        st.rerun()
                with detail_cols[1]:
                    st.markdown(f"**Tier:** {app.get('tier', 'N/A')}")
                    st.markdown(f"**Remote:** {app.get('remote', 'N/A')}")
                    st.markdown(f"**Score:** {app.get('score', 'N/A')}")
                    st.markdown(f"**Applied:** {app.get('applied_date', 'N/A')}")
                    st.markdown(f"**Follow-up:** {app.get('follow_up_date', 'N/A')}")
                    if app.get("url"):
                        st.link_button("View Job", app["url"], key=f"det_link_{app['id'][:8]}")

                if app["status"] in INTERVIEW_STAGES:
                    st.markdown("---")
                    st.markdown("#### 📝 Prep")
                    prep = get_prep(app["id"])
                    if not prep:
                        if st.button("Generate prep", key=f"genprep_{app['id'][:8]}"):
                            with st.spinner("Generating interview prep..."):
                                prep = generate_prep(app)
                                save_prep(app["id"], prep)
                            st.rerun()
                    else:
                        brief = prep.get("company_brief", "")
                        if brief:
                            st.markdown(f"**Company brief**\n\n{brief}")
                        qs = prep.get("likely_questions") or []
                        if qs:
                            st.markdown("**Likely questions**")
                            for q in qs:
                                st.markdown(f"- {q}")
                        stars = prep.get("star_stories_to_use") or []
                        if stars:
                            st.markdown("**STAR stories to use**")
                            for s in stars:
                                st.markdown(
                                    f"- **{s.get('question_type', '')}** — "
                                    f"{s.get('story', '')} _({s.get('key_metrics', '')})_"
                                )
                        topics = prep.get("system_design_topics") or []
                        if topics:
                            st.markdown("**System design topics**")
                            for t in topics:
                                st.markdown(f"- {t}")
                        asks = prep.get("questions_to_ask_them") or []
                        if asks:
                            st.markdown("**Questions to ask them**")
                            for q in asks:
                                st.markdown(f"- {q}")
                        tips = prep.get("role_specific_tips", "")
                        if tips:
                            st.markdown(f"**Tips**\n\n{tips}")
                        if st.button("Regenerate", key=f"regenprep_{app['id'][:8]}"):
                            with st.spinner("Regenerating interview prep..."):
                                prep = generate_prep(app)
                                save_prep(app["id"], prep)
                            st.rerun()

    # Stats section
    st.markdown("### Stats")
    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.metric("This Week", f"{stats['applied_this_week']}/{settings['weekly_target']}")
    with stat_cols[1]:
        total_applied = stats["total_applied"]
        callbacks = len([a for a in apps if a["status"] in ("phone_screen", "technical", "final_round", "offer")])
        rate = f"{int(callbacks / total_applied * 100)}%" if total_applied > 0 else "0%"
        st.metric("Response Rate", rate)
    with stat_cols[2]:
        st.metric("Active Pipeline", stats["active_pipeline"])
    with stat_cols[3]:
        st.metric("Total Applications", stats["total_applied"])


# ═══════════════════════════════════════════════════════════════════════
# TAB 4: DEBRIEF
# ═══════════════════════════════════════════════════════════════════════
with tab_debrief:
    st.markdown("### Today's Summary")

    daily_log = get_daily_log()
    apps_data = load_applications()

    # Summary table
    summary_cols = st.columns(5)
    scouted_count = sum(
        e.get("details", {}).get("new_roles", 0)
        for e in daily_log if e.get("action") == "scout_completed"
    )
    outreach_count = len([e for e in daily_log if e.get("action") == "outreach_generated"])
    applied_count = stats["applied_today"]
    fu_count = len([e for e in daily_log if e.get("action") == "followup_sent"])
    week_prog = f"{stats['applied_this_week']}/{settings['weekly_target']}"

    with summary_cols[0]:
        st.metric("Roles Scouted", scouted_count)
    with summary_cols[1]:
        st.metric("Outreach Generated", outreach_count)
    with summary_cols[2]:
        st.metric("Applications Logged", applied_count)
    with summary_cols[3]:
        st.metric("Follow-ups Sent", fu_count)
    with summary_cols[4]:
        st.metric("Week Progress", week_prog)

    # Tomorrow's priorities
    st.markdown("### Tomorrow's Priorities")

    if st.button("Generate Debrief", type="primary"):
        with st.spinner("Analyzing pipeline..."):
            from debrief import generate_debrief
            debrief_data = generate_debrief(daily_log, apps_data)
            st.session_state["debrief_data"] = debrief_data
        st.rerun()

    debrief_data = st.session_state.get("debrief_data")
    if debrief_data:
        priorities = debrief_data.get("tomorrow_priorities", [])
        if priorities:
            urgency_icons = {"high": "🔴", "medium": "🟡", "low": "🔵"}
            priority_html = ""
            for p in priorities:
                icon = urgency_icons.get(p.get("urgency", "medium"), "🔵")
                priority_html += f"<p style='color: #ccc; font-family: Inter, sans-serif; font-size: 0.9rem; margin: 0.4rem 0;'>{icon} {p['action']}</p>\n"

            st.markdown(f"""<div class="priority-box">{priority_html}</div>""", unsafe_allow_html=True)

        # Week over week
        st.markdown("### Week-over-Week Trend")
        wow = debrief_data.get("week_over_week", {})
        if wow:
            import pandas as pd
            weeks_sorted = sorted(wow.items())
            if weeks_sorted:
                df = pd.DataFrame(
                    [{"Week": f"W{k}", "Applications": v} for k, v in weeks_sorted]
                ).set_index("Week")
                st.bar_chart(df)

        # Motivation
        motivation = debrief_data.get("motivation", "")
        if motivation:
            st.markdown(f'<div class="motivation">{motivation}</div>', unsafe_allow_html=True)
    else:
        st.markdown("*Click **Generate Debrief** to get your daily summary and tomorrow's priorities.*")


# ═══════════════════════════════════════════════════════════════════════
# TAB 5: SETTINGS
# ═══════════════════════════════════════════════════════════════════════
with tab_settings:
    st.markdown("### Configuration")

    # ── 📝 Profile (editable resume/contact/targets) ──────────────────
    with st.expander("📝 Profile", expanded=True):
        # Parse RESUME_CONTEXT back into form fields (best-effort).
        def _seed_profile_values() -> dict:
            """Build a values dict from current WAR_PLAN, RESUME_CONTEXT, CONTACT_INFO."""
            headline = ""
            differentiators = ""
            skills = ""
            education = ""
            tone = settings.get("tone", "Warm, relationship-first")
            hard_rules = settings.get("hard_rules", "")

            try:
                lines = RESUME_CONTEXT.splitlines()
                if lines:
                    first = lines[0]
                    if " — " in first:
                        headline = first.split(" — ", 1)[1].strip()
                diffs = []
                for ln in lines:
                    s = ln.strip()
                    if not s:
                        continue
                    if s[:2].isdigit() or (s[:1].isdigit() and s[1:2] == "."):
                        diffs.append(s.split(".", 1)[1].strip())
                differentiators = "\n".join(diffs)
                for ln in lines:
                    if ln.startswith("SKILLS:"):
                        skills = ln.replace("SKILLS:", "", 1).strip()
                    elif ln.startswith("EDUCATION:"):
                        education = ln.replace("EDUCATION:", "", 1).strip()
                    elif ln.startswith("TONE:"):
                        tone_line = ln.replace("TONE:", "", 1).strip().rstrip(".")
                        if tone_line:
                            tone = tone_line
                    elif ln.startswith("DO NOT mention"):
                        hr = ln.replace("DO NOT mention", "", 1).strip().rstrip(".")
                        if hr and hr != "buzzwords you dislike":
                            hard_rules = hr
            except Exception:
                pass

            return {
                "name": CONTACT_INFO.get("name", ""),
                "email": CONTACT_INFO.get("email", ""),
                "phone": CONTACT_INFO.get("phone", ""),
                "linkedin": CONTACT_INFO.get("linkedin", ""),
                "github": CONTACT_INFO.get("github", ""),
                "website": CONTACT_INFO.get("website", ""),
                "headline": headline,
                "differentiators": differentiators,
                "skills": skills,
                "education": education,
                "target_roles": list(WAR_PLAN.get("target_roles", [])),
                "tier_1": "\n".join(WAR_PLAN.get("tier_1", [])),
                "tier_2": "\n".join(WAR_PLAN.get("tier_2", [])),
                "tier_3": "\n".join(WAR_PLAN.get("tier_3", [])),
                "target_comp": WAR_PLAN.get("target_comp", ""),
                "remote_preference": WAR_PLAN.get("remote_preference", "remote-first") == "remote-first",
                "weekly_target": WAR_PLAN.get("weekly_target", 10),
                "min_experience_years": WAR_PLAN.get("min_experience_years", 0),
                "max_experience_years": WAR_PLAN.get("max_experience_years", 5),
                "plan_days": WAR_PLAN.get("plan_days", 60),
                "start_date": WAR_PLAN.get("start_date", ""),
                "tone": tone,
                "hard_rules": hard_rules,
            }

        current_profile = _seed_profile_values()
        updated = render_profile_form(current_profile)

        if st.session_state.pop("_profile_form_submitted", False):
            try:
                new_resume = _build_resume_context(updated)
                new_plan = _build_war_plan(updated)
                new_contact = _build_contact_info(updated)
                _write_config_local(new_plan, new_resume, new_contact)
                st.toast("Profile saved ✓")
                st.rerun()
            except Exception as e:
                st.error(f"Could not save profile: {e}")

    # ── ⚙️ Automation toggles ──────────────────────────────────────────
    with st.expander("⚙️ Automation", expanded=False):
        with st.form("automation_form"):
            wide_net = st.toggle("Wide net mode — search beyond named companies", value=settings["wide_net"])
            auto_scout = st.toggle("Auto-scout — 7:00 AM daily, macOS notification", value=settings["auto_scout"])
            match_scoring = st.toggle("Match scoring — use Claude AI to score each role 1-10", value=settings["match_scoring"])
            referral_check = st.toggle("Referral check prompt — ask before cold outreach", value=settings["referral_check"])
            auto_followups = st.toggle("Auto-generate follow-ups for stale applications", value=settings["auto_followups"])
            remote_pref = st.toggle("Remote preference — prioritize remote roles", value=settings["remote_preference"])
            experience_filter = st.toggle("Experience filter — skip roles requiring 8+ years", value=settings["experience_filter"])
            auto_outreach_8plus = st.toggle(
                "Auto-generate outreach for 8+ matches (Rule 13)",
                value=settings.get("auto_generate_outreach_8plus", True),
            )

            if st.form_submit_button("Save automation", type="primary"):
                settings["wide_net"] = wide_net
                settings["auto_scout"] = auto_scout
                settings["match_scoring"] = match_scoring
                settings["referral_check"] = referral_check
                settings["auto_followups"] = auto_followups
                settings["remote_preference"] = remote_pref
                settings["experience_filter"] = experience_filter
                settings["auto_generate_outreach_8plus"] = auto_outreach_8plus
                _save_settings(settings)

                if auto_scout:
                    from scheduler import install
                    install()
                else:
                    from scheduler import uninstall
                    uninstall()

                st.toast("Automation saved ✓")
                st.rerun()

    # ── 🎨 Preferences (tone, rules, targets, sprint) ──────────────────
    with st.expander("🎨 Preferences", expanded=False):
        tone_options = ["Warm, relationship-first", "Direct and concise", "Technical and detailed"]
        current_tone = settings.get("tone", tone_options[0])
        tone_idx = tone_options.index(current_tone) if current_tone in tone_options else 0

        tone_pick = st.radio("Outreach tone", tone_options, index=tone_idx, key="pref_tone")
        hard_rules_val = st.text_area(
            "Hard rules (injected into every AI prompt)",
            value=settings.get("hard_rules", ""),
            height=100,
            key="pref_hard_rules",
        )
        weekly_target_val = st.number_input(
            "Weekly target (applications)",
            min_value=1, max_value=50,
            value=int(settings.get("weekly_target", 10)),
            key="pref_weekly_target",
        )

        current_sd = settings.get("start_date") or WAR_PLAN.get("start_date")
        try:
            sd_default = datetime.strptime(current_sd, "%Y-%m-%d").date()
        except Exception:
            sd_default = datetime.now().date()
        start_date_val = st.date_input("Start date (DAY X of N counter)", value=sd_default, key="pref_start_date")

        plan_days_val = st.number_input(
            "Sprint length (days)",
            min_value=7, max_value=365,
            value=int(settings.get("plan_days", 60)),
            key="pref_plan_days",
        )

        if st.button("Save preferences", type="primary", key="save_prefs_btn"):
            settings["tone"] = tone_pick
            settings["hard_rules"] = hard_rules_val
            settings["weekly_target"] = int(weekly_target_val)
            settings["start_date"] = start_date_val.isoformat()
            settings["plan_days"] = int(plan_days_val)
            _save_settings(settings)
            st.toast("Preferences saved ✓")
            st.rerun()

    # ── 🔑 API keys ────────────────────────────────────────────────────
    with st.expander("🔑 API keys", expanded=False):
        gemini_key_env = os.environ.get("GEMINI_API_KEY", "")
        perplexity_key_env = os.environ.get("PERPLEXITY_API_KEY", "")

        def _mask(k: str) -> str:
            if not k:
                return ""
            return k[:6] + "..."

        col_g, col_p = st.columns(2)
        with col_g:
            if gemini_key_env:
                st.markdown(f"**Gemini:** ✅ Connected `{_mask(gemini_key_env)}`")
            else:
                st.markdown("**Gemini:** ⚠️ Missing")
        with col_p:
            if perplexity_key_env:
                st.markdown(f"**Perplexity:** ✅ Connected `{_mask(perplexity_key_env)}`")
            else:
                st.markdown("**Perplexity:** ⚠️ Missing")

        new_gemini = st.text_input("GEMINI_API_KEY", type="password", key="settings_gemini_key")
        new_perplexity = st.text_input("PERPLEXITY_API_KEY", type="password", key="settings_perplexity_key")

        bcol1, bcol2, bcol3 = st.columns(3)
        with bcol1:
            if st.button("Update keys", key="update_keys_btn"):
                try:
                    if new_gemini.strip():
                        _upsert_env("GEMINI_API_KEY", new_gemini.strip())
                    if new_perplexity.strip():
                        _upsert_env("PERPLEXITY_API_KEY", new_perplexity.strip())
                    st.toast("Keys updated — restart app to apply ✓")
                except Exception as e:
                    st.error(f"Could not update keys: {e}")
        with bcol2:
            if st.button("Test Gemini", key="test_gemini_btn"):
                key_to_test = new_gemini.strip() or gemini_key_env
                ok, msg = _test_gemini(key_to_test)
                (st.success if ok else st.error)(msg)
        with bcol3:
            if st.button("Test Perplexity", key="test_pplx_btn"):
                key_to_test = new_perplexity.strip() or perplexity_key_env
                ok, msg = _test_perplexity(key_to_test)
                (st.success if ok else st.error)(msg)

    # ── 🔗 Integrations ────────────────────────────────────────────────
    with st.expander("🔗 Integrations", expanded=False):
        st.info("Notion sync coming soon — track roadmap in README.md")
        st.markdown("**Export Data**")
        csv_data = export_csv()
        if csv_data:
            st.download_button("Download CSV", csv_data, "war_room_export.csv", "text/csv")
        else:
            st.markdown("*No data to export yet.*")

    st.markdown("---")
    st.markdown("### Target Companies")
    st.markdown(f"**Tier 1:** {', '.join(WAR_PLAN['tier_1'])}")
    st.markdown(f"**Tier 2:** {', '.join(WAR_PLAN['tier_2'])}")
    st.markdown(f"**Tier 3:** {', '.join(WAR_PLAN['tier_3'])}")
    st.markdown(f"**Target Roles:** {', '.join(WAR_PLAN['target_roles'])}")

    st.markdown("---")
    st.markdown(f"<p style='color: #333; font-size: 0.7rem; text-align: center;'>WAR ROOM v1.0 — {CONTACT_INFO['name']}</p>", unsafe_allow_html=True)
