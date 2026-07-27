# Visapolicy.ai — Project Knowledge Base

## What This Project Does

Visapolicy.ai monitors USCIS and immigration-related rule changes published in the Federal Register, processes them using AI to extract plain-English summaries, and delivers personalized alerts to subscribers based on their immigration profile.

See `TECH_STACK.txt` for a full technology-choice writeup (what's used, why, and how).

---

## Project Structure

```
visapolicy/
├── run.py                          # Phase 1 pipeline entry point
├── requirements.txt                # Python dependencies
├── docker-compose.yml              # PostgreSQL container
├── .env                            # Your secrets (never commit this)
├── alembic.ini                     # Database migration config
├── alembic/
│   └── versions/
│       ├── 001_initial_schema.py   # Creates all base tables
│       ├── 002_expand_user_profile.py  # Adds full profile fields to users
│       └── 003_add_password_reset.py   # Adds reset_token / reset_token_expires to users
├── src/
│   ├── config.py                   # Reads .env into Settings object
│   ├── db/
│   │   ├── models.py               # SQLAlchemy table definitions
│   │   └── session.py              # DB connection + init_db()
│   ├── ingestion/
│   │   └── federal_register.py     # Federal Register API client
│   ├── processing/
│   │   └── extractor.py            # Groq AI extraction engine (chunks long docs)
│   ├── matching/
│   │   └── engine.py               # Profile-to-rule scoring engine
│   ├── alerts/
│   │   └── email.py                # HTML email builder + Resend sender (digests + password reset)
│   ├── api/
│   │   ├── main.py                 # FastAPI app
│   │   ├── dependencies.py         # JWT auth (header-based + SSE query-param fallback)
│   │   ├── rate_limit.py           # Shared slowapi Limiter instance
│   │   ├── schemas/                # Pydantic request/response models
│   │   └── routers/
│   │       ├── auth.py             # register/login/me + forgot-password/reset-password
│   │       ├── profile.py          # GET PATCH /profile
│   │       ├── dashboard.py        # GET /dashboard (personalized feed)
│   │       ├── changes.py          # GET /changes /changes/:id
│   │       └── stream.py           # GET /stream/alerts (SSE)
│   └── pipeline.py                 # Orchestrates all Phase 1 stages
├── scripts/
│   └── seed_user.py                # Add a test subscriber to the DB (no password — API-only)
└── frontend/
    ├── app/
    │   ├── page.tsx                # Login / Register page (+ forgot-password inline form)
    │   ├── reset-password/page.tsx # Set new password via emailed token
    │   ├── onboarding/page.tsx     # 5-step profile wizard (first-time setup)
    │   ├── profile/page.tsx        # Single-page profile editor (post-onboarding edits)
    │   └── dashboard/page.tsx      # Personalized change feed
    ├── components/
    │   ├── ChangeCard.tsx          # Expandable change with before/after diff
    │   ├── ImpactBadge.tsx         # Color-coded impact label
    │   ├── ProfileFields.tsx       # Shared field groups (visa/GC/employment/dependents/alerts)
    │   └── OnboardingWizard.tsx    # Multi-step wrapper around ProfileFields
    └── lib/
        ├── api.ts                  # Typed API client (fetch wrapper, throws ApiError w/ status)
        └── auth.ts                 # Token helpers (localStorage)
```

---

## Environment Variables (.env)

| Variable | Description | Where to get it |
|----------|-------------|-----------------|
| `DATABASE_URL` | PostgreSQL connection string | Already set for local Docker |
| `GROQ_API_KEY` | Groq API key for LLM extraction | console.groq.com → API Keys (free) |
| `RESEND_API_KEY` | Email delivery key | resend.com → API Keys |
| `RESEND_FROM_EMAIL` | Sender email address | Must be a verified domain in Resend — currently `onboarding@resend.dev` (sandbox) since `visapolicy.ai` isn't registered yet |
| `LOOKBACK_DAYS` | How many days back to scan | Default: 7 |
| `JWT_SECRET_KEY` | Signs/verifies login session tokens | Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` — required, no default |
| `FRONTEND_BASE_URL` | Used to build the link inside password-reset emails | Default: `http://localhost:3000` |

---

## How to Run

### Prerequisites
- Docker Desktop running (whale icon in menu bar)
- Python 3.12+ with Anaconda
- Node.js 18+ (for frontend)

### First-time setup

```bash
cd /Users/vidhipatel/visapolicy

# 1. Start PostgreSQL
docker compose up -d

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run database migrations
alembic upgrade head

# 4. Add your API keys to .env
#    ANTHROPIC_API_KEY=sk-ant-api03-...
#    RESEND_API_KEY=re_...

# 5. Add yourself as a test subscriber
#    Edit scripts/seed_user.py with your email + visa type, then:
python scripts/seed_user.py
```

### Run the pipeline

```bash
# Dry run (no emails sent) — good for testing
python run.py --days 30 --dry-run

# Live run (extracts changes + sends emails)
python run.py --days 7
```

### Run the API server (Phase 2)

```bash
uvicorn src.api.main:app --reload --port 8000
```

### Run the frontend (Phase 2)

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

---

## Data Flow (Phase 1)

```
1. Federal Register API
   → Fetches documents from USCIS, DHS, EOIR published in last N days
   → Filters to immigration-relevant documents by keyword

2. Full text fetch
   → Downloads the HTML body of each document
   → Converts to clean markdown text (strips nav/headers/footers)
   → Truncates to 80,000 characters for Claude's context window

3. Groq AI extraction (llama-3.3-70b-versatile)
   → Uses function calling (structured output) to extract rule changes
   → Each change includes: old_rule, new_rule, plain_english_summary,
     impact_level, action_required, visa_categories_affected, tags
   → action_required is coerced from string to bool after parsing (Llama quirk)

4. PostgreSQL storage
   → policy_documents table: one row per Federal Register document
   → rule_changes table: one row per extracted change

5. Profile matching
   → Queries all active users
   → Scores each change against each user's visa type, employer, GC stage, etc.
   → Users only receive alerts for changes that score above threshold (7.0)

6. Email delivery (Resend)
   → Sends one digest email per user with all matched changes
   → HTML email with before/after rule comparison, impact badges, action items
   → Logs delivery in alert_logs table
```

---

## Database Tables

### policy_documents
Stores raw metadata for each Federal Register document.

| Column | Type | Description |
|--------|------|-------------|
| id | String | UUID primary key |
| doc_number | String | Federal Register document number (e.g. 2026-08333) |
| title | Text | Full document title |
| source_url | Text | Link to the FR document |
| published_at | Date | Publication date |
| effective_at | Date | When the rule takes effect |
| overall_impact_level | String | low / medium / high |
| processed | Boolean | Whether Claude has run on this doc |

### rule_changes
One row per extracted change within a document.

| Column | Type | Description |
|--------|------|-------------|
| id | String | UUID primary key |
| document_id | String | FK to policy_documents |
| topic | Text | Short label (e.g. "Specialty Occupation Definition") |
| old_rule | Text | Exact prior rule text |
| new_rule | Text | Exact new rule text |
| plain_english_summary | Text | Non-lawyer explanation |
| impact_level | String | low / medium / high |
| action_required | Boolean | Does the user need to act? |
| visa_categories_affected | JSON | e.g. ["H-1B", "H-4 EAD"] |
| tags | JSON | Keyword tags for matching |

### users
Subscriber profiles with full immigration context.

Key fields: `primary_visa_type`, `gc_stage`, `priority_date`, `country_of_birth`,
`employer_type`, `placement_type`, `on_opt`, `opt_type`, `dependent_visa_types`,
`alert_frequency`, `min_impact_level`

Auth fields: `password_hash` (bcrypt), `reset_token` (SHA-256 hash of the emailed token,
not the raw value), `reset_token_expires` (1 hour from request). Users created via
`scripts/seed_user.py` have no `password_hash` and can't log into the API/web app until
they set one through the forgot-password flow.

### alert_logs
Tracks every alert sent, to which user, for which change.

---

## Matching Engine (Phase 2)

Located at `src/matching/engine.py`. Scores each rule change against a user's profile:

| Signal | Points | Condition |
|--------|--------|-----------|
| Direct visa category match | +10 | Change affects user's visa type |
| Tag-based visa match | +6 | Change tags overlap with visa keywords |
| Third-party placement | +5 | User at client site + site-visit rule |
| STEM OPT match | +6 | User on STEM OPT + STEM rule change |
| GC stage match | +5 | Change affects user's current GC stage |
| H-4 EAD dependent | +4 | User's dependent has H-4 EAD |
| Country of birth match | +4 | India/China user + priority date change |
| Employer type match | +3 | Consulting/staffing + LCA/site-visit rule |

Impact multipliers: High ×1.5, Medium ×1.2, Low ×1.0

Alert fires if final score ≥ 7.0

---

## API Endpoints (Phase 2)

Base URL: `http://localhost:8000/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/register | Create account (password: min 8 chars, letters + numbers) |
| POST | /auth/login | Get JWT token |
| GET | /auth/me | Get current user |
| POST | /auth/forgot-password | Request a reset email — always returns the same generic message, whether or not the email is registered |
| POST | /auth/reset-password | Set a new password using a valid (unexpired, single-use) reset token |
| GET | /profile | Get full profile |
| PATCH | /profile | Update profile fields |
| GET | /dashboard | Personalized feed with relevance scores |
| GET | /changes | All rule changes (filterable by impact/visa) |
| GET | /changes/:id | Single change detail |
| GET | /stream/alerts | SSE stream for real-time push notifications |

---

## Authentication & Security (Phase 2)

- **Passwords**: bcrypt via Passlib, never stored or logged in plaintext. Enforced (server-side, on both register and reset): minimum 8 characters, must mix letters and numbers.
- **Sessions**: JWT (HS256), 7-day expiry, signed with `JWT_SECRET_KEY` from `.env`. `src/api/dependencies.py` requires this to be set — the app won't start without it.
- **Forgot/reset password** (`src/api/routers/auth.py`):
  - `/auth/forgot-password` never reveals whether an email is registered — same generic response either way, to prevent account enumeration.
  - Reset token is `secrets.token_urlsafe(32)`; only its **SHA-256 hash** is stored in `users.reset_token` (same principle as password hashing — a DB leak alone can't be used to redeem an unexpired link). The raw token only ever exists in the emailed link.
  - 1-hour expiry, single-use (cleared after a successful reset).
- **Rate limiting** (`slowapi`, per-IP, via `src/api/rate_limit.py`): login 10/min, register 5/hr, forgot-password 5/hr, reset-password 10/min.
- **SSE auth** (`/stream/alerts`): accepts the token via `?token=` query param as a fallback to the `Authorization` header — needed because browser `EventSource` can't set custom headers. Scoped only to that one route (`get_current_user_sse`); every other route still requires the header.
- **Known gaps, not yet built**: no email verification on registration (anyone can register with an email they don't own), no account lockout beyond the per-IP rate limit, `localStorage`-stored JWT is readable by any JS on the page (XSS exposure — an `httpOnly` cookie would be safer).

---

## Federal Register API

- Base URL: `https://www.federalregister.gov/api/v1`
- No authentication required
- Agency slugs used:
  - `u-s-citizenship-and-immigration-services` (USCIS)
  - `executive-office-for-immigration-review` (EOIR)
  - `homeland-security-department` (DHS)
  - `u-s-customs-and-border-protection` (CBP)
  - `u-s-immigration-and-customs-enforcement` (ICE)

---

## Known Issues & Fixes Applied

| Issue | Fix |
|-------|-----|
| `docker-compose` not found | Use `docker compose` (space, not hyphen) — Docker v2 syntax |
| Docker not in PATH | Run: `export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin"` |
| Federal Register 400 error | Wrong agency slug — was `homeland-security`, correct is `homeland-security-department` |
| Groq returns `action_required` as string `"true"`/`"false"` instead of boolean | Coerce after JSON parse: `change["action_required"] = change["action_required"].lower() == "true"` |
| Ingestion crashed on FR documents with `abstract: null` | `.get("abstract", "")` only covers a *missing* key, not an explicit `null` — use `item.get("abstract") or ""` |
| Groq 413 error on long documents (12,000 tokens/min free-tier cap, one doc alone can exceed it) | Chunk documents over ~20,000 chars into multiple extraction calls on paragraph boundaries, merge results (`src/processing/extractor.py`) |
| API crashed on startup: `email-validator is not installed` | `EmailStr` needs it but it was missing from `requirements.txt` entirely — added `email-validator>=2.0.0` |
| Real-time SSE alerts always 401'd from the actual dashboard | Browser `EventSource` can't set custom headers, but `get_current_user` only checked `Authorization` — added a query-param fallback scoped to `/stream/alerts` only |
| Login crashed with 500 for any account with no password set (e.g. users from `seed_user.py`) | `passlib.verify()` can't identify an empty-string hash and raises instead of returning False — guard with `not user.password_hash` before calling verify |
| Onboarding wizard always opened blank, even when editing an existing profile | Wasn't loading current profile data — `/onboarding` and the new `/profile` page now pre-fill from `getProfile()` |
| JWT signing secret was hardcoded in source (`src/api/dependencies.py`) | Moved to `.env` as `JWT_SECRET_KEY`, required with no fallback default |
| `visapolicy.ai` domain not verified in Resend (blocks all real sends) | `visapolicy.ai` isn't actually registered with any registrar (confirmed via whois) — using `onboarding@resend.dev` sandbox sender until a real domain is bought and verified |

---

## AI Model Decision

We switched from **Anthropic Claude** to **Groq (llama-3.3-70b-versatile)** as the extraction engine.

**Why Groq over Claude:**
- Claude requires a paid API key; Groq has a generous free tier (14,400 requests/day)
- The developer's machine is an M1 MacBook Air with 8GB RAM — not enough to run a capable model locally via Ollama
- Groq runs 70B parameter models on their cloud infrastructure, giving much better extraction quality than any model that fits in 8GB locally
- Federal Register documents are public, so sending them to Groq's servers is fine

**Why not Ollama (local):**
- 8GB unified memory on M1 Air is shared with OS + apps (~3-4GB used at idle)
- Only ~4GB left for a model — limits to 7B models which struggle with structured JSON extraction from dense 80,000-character legal documents

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | Complete | Ingestion + Groq/Llama extraction + PostgreSQL + email digest |
| Phase 2 | Complete | FastAPI backend + JWT auth + profile onboarding + Next.js dashboard + SSE alerts |
| Phase 3 | Planned | RAG-powered AI chat assistant ("how does this affect me?") |
| Phase 4 | Planned | Mobile app, attorney integrations, priority date tracker |
