# Visapolicy.ai

**Real-time, AI-powered USCIS/immigration policy alerts** turns dense Federal Register legal text into plain-English "does this affect me?" digests, personalized to each user's visa status, green card stage, employer type, and dependents.

Every day, USCIS, DHS, EOIR, CBP, and ICE publish rule changes that can directly affect an immigrant's legal status — a new site-visit requirement, a changed OPT rule, a shifted priority date. Almost none of it is written for a non-lawyer, and there's no single place that tells you *"this specific change affects you."* Visapolicy.ai automates that: it watches the Federal Register, uses an LLM to extract structured rule changes (not just a summary the exact before/after text, impact level, and who's affected), and scores each change against a user's actual profile before ever surfacing it.

## Architecture

```
Federal Register API  →  Clean + chunk document text  →  LLM extraction (function-calling)
                                                                    │
                                                                    ▼
                                                          PostgreSQL (documents + changes)
                                                                    │
                                              ┌─────────────────────┼─────────────────────┐
                                              ▼                     ▼                     ▼
                                     Relevance scoring        Email digests          Live dashboard
                                     (per-user, multi-signal)   (Resend)          + SSE real-time push
```

- **Ingestion**: polls the Federal Register's public API for USCIS-relevant documents, strips HTML boilerplate, converts to clean text.
- **Extraction**: Groq (Llama 3.3 70B) extracts every distinct rule change via structured function-calling — exact `old_rule`/`new_rule` text, plain-English summary, impact level, affected visa categories. Documents that exceed the LLM provider's per-request token limit are automatically chunked on paragraph boundaries and the results merged, so long rules (some over 80,000 characters) are never silently truncated.
- **Storage**: PostgreSQL via SQLAlchemy + Alembic migrations.
- **Relevance scoring**: a deterministic, multi-signal engine (`src/matching/engine.py`) scores each change against a user's visa type, green card stage, employer type, placement type, OPT status, dependents, and country of birth — not a single visa-category filter, but weighted signals that combine (e.g. "third-party placement + site-visit rule" or "STEM OPT + STEM rule change").
- **Delivery**: daily/weekly email digests (Resend) plus a live Next.js dashboard with Server-Sent-Events push for real-time alerts.

## Features

- Monitors 5 federal agencies (USCIS, DHS, EOIR, CBP, ICE) for immigration-relevant rule changes
- AI-extracted before/after rule comparisons — not just a summary, the actual legal text diff
- Personalized relevance scoring across 8+ profile signals, not a single visa-type filter
- Daily/weekly email digests with impact-sorted, action-required callouts
- Full auth system: registration, login, forgot/reset password — rate-limited and hardened (see below)
- Real-time dashboard with SSE push notifications
- 5-step onboarding wizard + single-page profile editor for updating your immigration profile

## Security

- Passwords hashed with bcrypt; never stored or logged in plaintext
- Server-side password strength enforcement (min 8 characters, mixed letters/numbers)
- JWT sessions signed with a required (no hardcoded fallback) secret from environment config
- Password reset tokens are single-use, expire in 1 hour, and are stored as a **SHA-256 hash** — a database leak alone can't be used to redeem an unexpired reset link
- Forgot-password endpoint returns an identical response whether or not the email is registered, preventing account enumeration
- Per-IP rate limiting on all auth endpoints (login, register, forgot/reset password) via `slowapi`

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL |
| AI extraction | Groq (`llama-3.3-70b-versatile`), structured function-calling |
| Email | Resend |
| Auth | JWT (python-jose), bcrypt (Passlib), slowapi rate limiting |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Infra | Docker Compose (local Postgres) |

Full rationale for every technology choice — including the tradeoffs and the real bugs hit along the way — is in [`TECH_STACK.txt`](./TECH_STACK.txt).

## Getting Started

### Prerequisites
- Docker Desktop
- Python 3.12+
- Node.js 18+

### Setup

```bash
git clone https://github.com/viiddhi/visapolicy-ai.git
cd visapolicy-ai

# 1. Start PostgreSQL
docker compose up -d

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Fill in GROQ_API_KEY, RESEND_API_KEY, and generate JWT_SECRET_KEY:
python3 -c "import secrets; print(secrets.token_hex(32))"

# 4. Run database migrations
alembic upgrade head
```

### Run the ingestion pipeline

```bash
python run.py --days 30 --dry-run   # extract only, no emails sent
python run.py --days 7               # live run
```

### Run the API + frontend

```bash
uvicorn src.api.main:app --reload --port 8000

cd frontend
npm install
npm run dev   # http://localhost:3000
```

Full setup detail, database schema, API reference, and the relevance-scoring formula are documented in [`knowledge.md`](./knowledge.md).

## Roadmap

| Phase | Status | Description |
|---|---|---|
| 1 | Complete | Federal Register ingestion, LLM extraction, PostgreSQL, email digests |
| 2 | Complete | FastAPI backend, JWT auth, profile onboarding, Next.js dashboard, SSE alerts |
| 3 | Planned | RAG-powered chat assistant ("how does this affect me?") |
| 4 | Planned | Mobile app, attorney integrations, priority date tracker |

## Author

Built by [Vidhi Patel](https://github.com/viiddhi).
