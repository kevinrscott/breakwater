# Breakwater

**A personal job-discovery tool for early-career candidates, built to a security-conscious, production-minded engineering standard.**

## The problem

Most job boards are weak at answering the questions that actually matter for an early-career search:

- Is this job actually junior or early-career?
- Is the listed experience truly required, merely preferred, or ambiguous?
- Does "remote" actually include applicants in Canada?
- Is a hybrid job realistically close enough to commute to?
- Is this the same posting already seen elsewhere?
- Is this a realistic opportunity, a stretch, or clearly unsuitable?
- What's new since the last search?

Breakwater collects jobs from permitted APIs and public employer job-board endpoints, normalizes them, classifies them using deterministic and explainable rules, and surfaces a focused daily review queue — with the reasoning behind every classification stored and visible.

## Status

**v0 in progress.** The current focus is a small, personally-usable Django application: one validated job source, rule-based classification, and a Django Admin review dashboard. See [`docs/v0-spec.md`](docs/v0-spec.md) for exact scope and [`docs/vision.md`](docs/vision.md) for the full problem statement and product principles.

A public-facing v1 (Next.js frontend, multiple sources, PostGIS, evaluated classifiers) is planned once v0 proves useful in a real job search — see [`docs/roadmap.md`](docs/roadmap.md).

## How this was built

Development uses AI-assisted coding under explicit review discipline — one issue at a time, a stated plan before changes, tests, and manual diff review before merge. See [`AGENTS.md`](AGENTS.md) for the exact constraints the agent works under.

## Setup

The current workspace runs Django on the host and connects to an existing PostgreSQL server. Docker Compose is not included yet.

Prerequisites:

- Python 3.12
- [`uv`](https://docs.astral.sh/uv/)
- PostgreSQL with a database and user available for local development

From the repository root, create the local environment file:

```powershell
cd app
copy .env.example .env
```

Edit `app/.env` to match the local PostgreSQL database and replace the development-only secret placeholder. The settings require all of these variables:

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Local Django signing key; use a unique secret outside this example |
| `DJANGO_DEBUG` | `true` or `false` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names accepted by Django |
| `POSTGRES_DB` | PostgreSQL database name |
| `POSTGRES_USER` | PostgreSQL user |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_HOST` | PostgreSQL server host name |
| `POSTGRES_PORT` | PostgreSQL server port |

Install dependencies, validate the Django configuration, and apply Django's initial migrations:

```powershell
uv sync
uv run python manage.py check
uv run python manage.py migrate
```

Start the development server:

```powershell
uv run python manage.py runserver
```

The development server then listens at `http://127.0.0.1:8000/`. Stop it with `Ctrl+C`.

## Documentation

| Doc | Purpose |
|---|---|
| [`docs/vision.md`](docs/vision.md) | The problem, priorities, and product principles |
| [`docs/v0-spec.md`](docs/v0-spec.md) | The exact v0 build spec — data model, classification rules, definition of done |
| [`docs/roadmap.md`](docs/roadmap.md) | Where this goes after v0 is validated |
| [`docs/source-notes.md`](docs/source-notes.md) | Evaluation and selection record for the first job-data source |
| [`docs/usage-log.md`](docs/usage-log.md) | Findings from real-world use once v0 is functional |
| [`AGENTS.md`](AGENTS.md) | Workflow and rules for AI-assisted contributions |
