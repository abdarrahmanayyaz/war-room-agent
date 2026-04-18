# war-room-agent

A local AI-powered job-search agent. Scouts roles from direct ATS APIs and Perplexity, scores each match against your resume with Gemini, drafts tailored outreach (cover letters, LinkedIn DMs, cold emails), generates event-aware follow-ups grounded in recent company news, auto-prepares interview packets when a status moves to phone screen, and runs an end-of-day debrief with tomorrow's priorities.

Runs entirely on your laptop. JSON-file persistence, no database. Built with Streamlit, Google Gemini, and Perplexity Sonar.

---

## Why this exists

Most job-search tools automate the wrong side of the problem — they help you fire off more generic applications. This one is built for the opposite: fewer applications, each of them dramatically more tailored, informed by real company context, and tracked end-to-end.

---

## Features

- **4-layer scout** — Layer 0 hits ATS APIs (Greenhouse, Lever, Ashby) directly for your named targets so you get real, current postings with zero hallucination risk; Layers 1-3 use Perplexity Sonar to sweep broader sources.
- **Match scoring** — every new role scored 1-10 against your resume via Gemini 2.5 Flash with reasoning + strengths + gaps.
- **Tailored outreach** — cover letter, LinkedIn DM, cold email, 3-4 resume bullets, and suggested titles to target, per role. Role-type-aware (FDE emphasizes different differentiators than DevRel).
- **Event-aware follow-ups** — before generating a stale-app follow-up, Perplexity pulls recent company news (product launches, funding, milestones) so messages reference real context instead of saying "just checking in."
- **Auto interview prep** — when an application status changes to `phone_screen` / `technical` / `final_round`, the app auto-generates a prep packet: company brief, likely questions, STAR stories to use, system design topics, questions to ask them, stage-specific tips.
- **Kanban tracker** — standard pipeline (To Apply → Applied → Referral → Phone Screen → Technical → Final → Offer/Rejected) with response rates and weekly velocity.
- **Daily debrief** — end-of-day summary + 3-5 prioritized actions for tomorrow + week-over-week trend.
- **Dedup + filtering** — SHA-256 hashing by `company|role|url`, exclude patterns for PhD-required / 8+ years / internships / clearance-only, include patterns focused on AI / LLM / solutions / FDE / DevRel titles.
- **macOS auto-scout** — optional `launchd` plist runs the scout daily at 7am and fires a notification.

---

## Architecture

```
app.py (Streamlit UI — 5 tabs)
  │
  ├─ scout.py         Layer 0: Greenhouse/Lever/Ashby JSON APIs (24h cache)
  │                   Layers 1-3: Perplexity Sonar sweeps
  ├─ scorer.py        Gemini 2.5 Flash — 1-10 match score
  ├─ tailor.py        Gemini 2.5 Pro — cover letters, outreach
  ├─ followup.py      Perplexity (news) + Gemini 2.5 Pro — event-aware follow-ups
  ├─ interview_prep.py Perplexity (research) + Gemini 2.5 Pro — prep packets
  ├─ debrief.py       Gemini 2.5 Flash — daily summary + priorities
  ├─ tracker.py       applications.json + daily_log.json CRUD
  └─ scheduler.py     macOS launchd auto-scout installer

data/
  scouted.json        All jobs ever discovered (deduped)
  applications.json   Your pipeline
  outreach.json       Generated outreach per role
  followups.json      Generated follow-ups per application
  interview_prep.json Prep packets per application
  daily_log.json      Timestamped activity log
  settings.json       UI settings
  .ats_cache/         24h cache for ATS API responses
```

All API calls funnel through `llm.py`, which exposes two helpers:

- `gemini_json(prompt, model, system, max_tokens)` — JSON-mode Gemini with `response_mime_type="application/json"`
- `perplexity_search(query, model, max_tokens)` — Perplexity Sonar with structured JSON output

---

## Providers & cost

| Task | Provider | Model | Typical daily cost |
|------|----------|-------|--------------------|
| Job discovery (web-grounded) | Perplexity | Sonar | $0.02-0.03 |
| Match scoring | Google | Gemini 2.5 Flash | < $0.01 |
| Cover letters / outreach | Google | Gemini 2.5 Pro | $0.05-0.10 |
| Follow-ups (with news lookup) | Google | Gemini 2.5 Pro + Perplexity Sonar | $0.02-0.03 |
| Interview prep | Google | Gemini 2.5 Pro + Perplexity Sonar | $0.05-0.10 (only on status change) |
| Daily debrief | Google | Gemini 2.5 Flash | < $0.01 |

Target pace of 10 apps/week works out to roughly **$0.10-0.20/day**.

---

## Setup

### Prerequisites

- Python 3.11+
- macOS or Linux
- [Gemini API key](https://aistudio.google.com/apikey) (AI Studio, free tier available)
- [Perplexity API key](https://www.perplexity.ai/settings/api)

### Install

```bash
git clone https://github.com/<your-username>/war-room-agent.git
cd war-room-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure

1. **API keys** — copy the template and paste your keys:
   ```bash
   cp .env.example .env
   # then edit .env
   ```
2. **Your resume and targets** — copy the template and edit:
   ```bash
   cp config_local.example.py config_local.py
   # edit config_local.py: WAR_PLAN, RESUME_CONTEXT, CONTACT_INFO
   ```
   `config_local.py` is gitignored. Anything it defines overrides the generic defaults in `config.py`.

3. **(Optional) Auto-scout daily at 7am** (macOS):
   ```bash
   python scheduler.py install
   ```

### Run

```bash
streamlit run app.py
```

Then open http://localhost:8501.

---

## Daily flow

1. **Morning** — launchd auto-scouts (or click Scout). Direct ATS results rank first, then Perplexity. Each new role is scored automatically.
2. **Review** — Scout tab. For 7+ scored roles, generate outreach, copy the cover letter, apply on the company's site, mark Applied.
3. **Interview** — move a card to Phone Screen and the prep packet auto-generates. Expand the card to read it.
4. **Follow-ups** — on day 7/14/21 after applying, the Follow-ups tab surfaces stale apps with draft messages that reference recent company news.
5. **Evening** — Debrief tab. See today's activity and tomorrow's priorities.

---

## Customization

All personalization lives in `config_local.py`. Edit three things:

- **`WAR_PLAN`** — target roles, tier 1/2/3 companies, keywords, weekly target, start date
- **`RESUME_CONTEXT`** — a plain-text brief the prompts use to tailor every generation
- **`CONTACT_INFO`** — name, email, LinkedIn, GitHub

Adding a company to `WAR_PLAN["tier_1"]` automatically means:
- Perplexity Layer 1 queries for it
- If its Greenhouse/Lever/Ashby slug is in `scout.py:ATS_MAP`, Layer 0 pulls real-time postings

To add a new direct-API company, extend `ATS_MAP` in `scout.py`. Greenhouse works for most big AI companies; check `boards-api.greenhouse.io/v1/boards/<slug>/jobs` first.

---

## Roadmap

- [ ] Notion integration for two-way pipeline sync
- [ ] Auth-gated remote mode (Fly.io / Railway deploy)
- [ ] Referral graph from LinkedIn export
- [ ] Anthropic Claude as an optional provider
- [ ] Salary estimation via levels.fyi API
- [ ] Interview-prep voice mode (text-to-speech mock interview)

---

## Security

- `.env` and `config_local.py` are gitignored. Never commit secrets or personal info.
- `data/*.json` is gitignored by default (contains your actual application history).
- The app runs on localhost only. If you expose it publicly, add auth.

---

## License

MIT — see [LICENSE](LICENSE).
