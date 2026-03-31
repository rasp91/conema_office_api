# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Röchling Office API — a REST API for managing guest registration with PDF form generation, dynamic HTML/Jinja2 form templates, and user administration for a Röchling office location.

## Tech Stack

- **Runtime**: Python 3.11
- **Framework**: FastAPI + Uvicorn (ASGI)
- **Database**: MySQL via SQLAlchemy ORM + PyMySQL driver
- **Auth**: JWT (python-jose) + bcrypt (passlib), API key header
- **Validation**: Pydantic v2 + pydantic-settings
- **PDF Generation**: WeasyPrint + Jinja2
- **Code Style**: black + isort (line length 140, configured in `pyproject.toml`)

## Key Directories

| Path | Purpose |
|------|---------|
| `src/app.py` | FastAPI app init, CORS, global exception handler, router registration |
| `src/config.py` | `pydantic_settings.BaseSettings` singleton loading from `.env` |
| `src/logger.py` | Dual console + file logger setup |
| `src/auth/` | JWT token management, role guards (`get_auth_user`, `get_admin_user`), login/register endpoints |
| `src/database/` | SQLAlchemy engine, session factory (`get_db`), Base class, ORM models |
| `src/v1/forms/` | Form template CRUD (HTML/Jinja2 content stored as LONGTEXT) |
| `src/v1/guest_book/` | Guest registration endpoints + PDF generation (`form.py`) |
| `src/v1/database/` | Admin-only database rebuild endpoint |
| `alembic/` | Migration scripts; `env.py` wires `DATABASE_URL` + `Base.metadata` |

## Essential Commands

```bash
# Run development server
uvicorn src.app:app --reload --host 0.0.0.0 --port 8005

# Install dependencies
pip install -r requirements.txt

# Generate a new migration after model changes
python -m alembic revision --autogenerate -m "description"

# Apply all pending migrations
python -m alembic upgrade head

# Rollback one migration
python -m alembic downgrade -1

# Check current migration state
python -m alembic current

# Format code
black src/
isort src/

# Docker build and run
docker build --no-cache -t roechling-office-fastapi-app:latest .
docker-compose up -d
```

No test suite exists in this project.

## Authentication

Three separate auth layers — all three may be required simultaneously on a single request:

1. **API key** — `API-KEY` header (`config.API_KEY`). Required on all `/v1/forms` and `/v1/guest-book` endpoints.
2. **JWT** — OAuth2 bearer token from `POST /auth/login`. Required for data access within those routes and all `/auth` management endpoints. Admin-only routes use `get_admin_user` dependency.
3. **DB key** — `DB-KEY` header (`config.DATABASE_KEY`). Required only on `/v1/database` endpoints.

## Database

MySQL database `roechling_office`. Models defined in `src/database/models.py`:

- **users** — bcrypt-hashed passwords, `is_admin` flag, `remember_token`
- **forms** — HTML/Jinja2 templates as LONGTEXT, FK to creator/updater users
- **guest_book** — visitor registrations; generated PDF stored as BLOB in `pdf_file`
- **variables** — key/value config store

Session factory uses pool pre-ping and 3600s recycle. Injected via `get_db()` FastAPI dependency.

## PDF Generation

`src/v1/guest_book/form.py` fetches the relevant `Form` template from the database, renders it with Jinja2 (injecting guest data and a base64 signature image), converts to PDF via WeasyPrint, and stores the PDF blob back into the `guest_book` row.

## Git Branching Workflow

- **Main branch:** `master` — all work happens here unless instructed otherwise.

Do NOT create feature/fix branches unless explicitly asked.

When the user requests a separate branch:

1. Create from `master`: `git checkout -b feature/short-description master`
2. Do the work, commit with descriptive messages
3. Push and create a PR into `master`

Branch naming (when requested):

- Features: `feature/add-variable-endpoint`
- Bug fixes: `fix/pdf-generation-encoding`
- Refactors: `refactor/extract-auth-dependency`

### Peer Review (all commits)

Before every commit or push, perform a peer review:

- Summarize all changes
- Flag potential issues (bugs, type errors, missing edge cases)
- Suggest improvements if any
- After the review, **wait for the user to confirm** before committing or pushing

## Additional Documentation

| File | When to check |
|------|---------------|
| [.env.template](.env.template) | Adding new configuration variables |
| [README.md](README.md) | Setup and deployment instructions |
