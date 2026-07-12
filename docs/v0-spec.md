# v0 Specification — Personal Utility

This is the doc to build from. If something isn't in here, it doesn't belong in v0 — check [`vision.md`](vision.md) for why, and [`roadmap.md`](roadmap.md) for when it's coming.

## Goal

Get real leads into daily use quickly, using one validated source and a small Django app usable for a real job search this week.

## Definition of done

- [ ] One command imports jobs from one validated source
- [ ] Re-running the import does not create duplicate rows
- [ ] Jobs show required and preferred experience when extractable
- [ ] Obvious senior jobs are classified appropriately
- [ ] Remote-Canada eligibility is classified as yes, no, or unclear
- [ ] Hybrid distance works for supported locations
- [ ] Jobs show a match band and readable explanation
- [ ] Classification evidence is preserved
- [ ] New jobs can be distinguished from previously reviewed jobs
- [ ] Jobs can be saved, hidden, and marked applied
- [ ] The original posting can be opened
- [ ] Core classification and import behaviour has automated tests
- [ ] A small CI workflow runs those tests, plus secret and dependency scanning
- [ ] Source content is rendered as plain text (or sanitized), never as raw HTML
- [ ] The tool has been used for at least one real week of job searching

The week of usage isn't a development freeze — fix bugs, tune rules, and record false positives/negatives, wrong extractions, and missing filters as you go. That evidence decides v1 priorities.

## Non-goals (do not build these in v0)

Next.js, PostGIS, multiple job sources, similarity-based deduplication, Redis, Celery, resume uploads, semantic search, authentication, multiple users, public deployment, email alerts, full application-history tracking, complex company normalization, machine-learning classification.

## Stack

Python, Django, PostgreSQL, Docker + Docker Compose, a committed dependency lockfile (e.g. `uv.lock`), a pinned Python version, a pinned PostgreSQL image version, Django Admin, pytest + pytest-django, Ruff, GitHub Actions, gitleaks (secret scanning), pip-audit (dependency scanning), one import management command.

PostgreSQL from day one — SQLite would create differences in JSON handling, constraints, text search, migrations, and later PostGIS adoption that aren't worth introducing.

## Security baseline (applies from v0, not just at deployment)

**Third-party content is untrusted.** Job descriptions may contain raw HTML or scripts. Render as plain text by default. If formatting is preserved later, sanitize server-side (e.g. `bleach`) before storage or display. Never use Django's `|safe` or React's `dangerouslySetInnerHTML` on unsanitized source content.

**Django configuration hygiene**, enforced before any non-local deployment: `SECRET_KEY` from an environment variable and never committed; `.env` excluded from Git with only `.env.example` (placeholders) committed; `DEBUG = False` outside local dev; `ALLOWED_HOSTS` set explicitly; secure cookie/CSRF settings once served over HTTPS.

**CI enforcement, not just written rules.** Secret scanning (gitleaks) on every push, plus an optional local pre-commit scan. If a credential is ever exposed, rotate it immediately — CI can catch it quickly but can't stop it from having entered history. Dependency vulnerability scanning (pip-audit, later npm audit) alongside Ruff and pytest.

**Outbound requests to job sources.** Explicit timeouts on every HTTP call, capped retry-with-backoff on transient failures, clear failure rather than hanging. If one adapter covers multiple employer boards, one failing board must not block the rest.

## Architecture

```
Django Admin / Simple Django View
  -> New jobs, search & filtering, classification evidence,
     save/hide/applied actions, original application links
        |
Django Application
  -> Import command, source adapter, normalization,
     experience/seniority/remote classification, location matching
        |
PostgreSQL
  -> Jobs, optional employer sources, review state, raw source payloads
```

v0 is a modular monolith — simple doesn't mean everything lives in one management command.

## Repository structure

```
breakwater/
├── app/
│   ├── config/
│   ├── breakwater/
│   │   ├── jobs/               (admin.py, models.py, services.py, management/commands/import_jobs.py)
│   │   ├── ingestion/          (adapters/, normalization.py, types.py)
│   │   ├── classification/     (experience.py, seniority.py, remote.py, matching.py, types.py)
│   │   └── locations/          (cities.py, distance.py)
│   ├── tests/
│   ├── manage.py
│   └── pyproject.toml
├── docs/
├── .github/workflows/backend.yml
├── compose.yaml
├── Dockerfile
├── .env.example
├── AGENTS.md
└── README.md
```

Don't create `apps/web` until the frontend actually exists.

## Source selection

Source quality is the most important early unknown — validate before building the importer.

**Half-day source check:** test one broad source and one direct-employer ATS option, inspecting ~30–50 postings each where possible. Evaluate: number of relevant Canadian jobs, full description vs. snippet availability, stable job identifiers, original application URLs, publication dates, location quality, remote-country information, experience wording, duplicate frequency, rate limits, and terms/attribution requirements.

**Path A — broad discovery source:** if a broad API produces enough relevant Canadian jobs. v0 includes one broad source adapter, configured search queries, search-result import, partial-description detection, and rate-limit handling — no employer registry yet.

**Path B — employer ATS source:** if direct employer boards produce meaningfully better data. v0 includes one ATS adapter and five-to-ten target employers (adds the `EmployerSource` model below).

## Data model

### Job

```
id
source_type, source_job_id, source_url, application_url
title, company_name, location_text, description_text, description_html_raw, content_completeness
posted_at, first_seen_at, last_seen_at, last_changed_at, is_active
years_required_min, years_required_max, years_preferred, experience_requirement_type
remote_canada_eligibility, remote_countries, workplace_type
office_latitude, office_longitude, distance_km_from_origin
career_track, role_family, match_band
classifier_version, classification_explanation, classification_evidence
raw_payload, raw_payload_hash
first_viewed_at, saved_at, hidden_at, applied_at, notes
created_at, updated_at
```

**Constraints:** `source_job_id` NOT NULL, NOT BLANK; `UNIQUE(source_type, source_job_id)` — the primary protection against duplicate rows on reimport. If a source doesn't provide a stable ID, derive one deterministically from documented stable fields (e.g. canonical application URL, or a normalized combination of source/company/title/location/publication identifier). Never generate a random ID per import.

**Content completeness:** `FULL / PARTIAL / SNIPPET / UNKNOWN`. A partial description must reduce classification confidence. `description_text` is the only field used for classification and default rendering; `description_html_raw` is preserved only for audit/reprocessing and must never be rendered directly.

**Review state:** don't use one mutually-exclusive status field — a job can be viewed-and-saved, saved-and-applied, applied-and-later-expired, etc. Use the four timestamps above. A job is "new" when `first_viewed_at IS NULL`.

### EmployerSource (Path B only)

```
id, company_name, source_type, board_identifier, careers_url,
is_active, last_import_at, last_success_at, consecutive_failures,
notes, created_at, updated_at
```

> **Open gap:** `career_track`, `role_family`, and `workplace_type` are in the model and referenced throughout (ingestion flow, admin filters, match-band logic) but don't have classification rules written anywhere yet — unlike experience, seniority, and remote eligibility below, which each have one. Worth writing before Step 6 of the implementation order.

## Ingestion design

The management command orchestrates the import; it doesn't contain the business logic.

**Flow:** fetch raw jobs → validate source fields → normalize → calculate payload hash → classify experience → classify seniority → classify remote eligibility → resolve known location → calculate distance if possible → determine career track → determine match band → upsert on `source_type + source_job_id` → set first_seen/last_seen/last_changed.

**Adapter contract:**

```python
class JobSourceAdapter(Protocol):
    source_name: str
    def fetch_jobs(self) -> Iterable[RawJob]: ...
    def normalize_job(self, raw_job: RawJob) -> NormalizedJobInput: ...
```

Even with one adapter in v0, this contract keeps the management command from becoming source-specific. `fetch_jobs` applies an explicit timeout and a capped retry-with-backoff policy; a failed single-source import terminates with a clear error rather than hanging. Multi-board ATS adapters isolate failures per board.

**Idempotent reimports:** create on new source ID, update `last_seen_at` on existing, update the record only when the payload hash changes, set `last_changed_at` only on meaningful content changes, and never overwrite user notes or reset saved/hidden/viewed/applied state.

## Experience classification

Store separately: `years_required_min`, `years_required_max`, `years_preferred`, `experience_requirement_type` (`REQUIRED / PREFERRED / NICE_TO_HAVE / FLEXIBLE / AMBIGUOUS / NOT_FOUND`).

Examples: "1+ years required" → `required_min = 1`. "1–2 years of professional experience" → `required_min = 1, required_max = 2`. "2 years preferred" → `preferred = 2, type = PREFERRED`. "Experience with Python" → no numeric requirement. "5 years of combined education and experience" must **not** automatically become 5 professional years.

**Match bands:**

- **MATCH** — junior/entry-level/new-grad/associate/internship language, 0–1 years required, no leadership signals.
- **POSSIBLE** (the default useful queue) — 0–2 years required, up to 3 preferred, flexible equivalent-experience wording, no clear senior ownership.
- **STRETCH** — 2–3 years required, strong role fit, no staff/lead/architect/manager/director expectations or team-management responsibility; explanation states why it's a stretch.
- **NOT_A_MATCH** — senior/staff/principal/lead/architect/manager/director title, 4+ years explicitly required, team-management or hiring responsibility, org-wide or strategic technical ownership.
- **UNCLEAR** — snippet-only content, conflicting required/preferred wording, unextractable experience, title/responsibilities disagree. Stays reviewable.

## Seniority classification

Strong negative signals: senior, staff, principal, lead engineer, architect, manager, director, head of, "manage a team," "performance management," "hire engineers," "set organization-wide strategy," "own engineering standards."

Must be contextual — "lead a small feature" isn't automatically Lead-level, but "Lead Engineer" is a strong signal, and "mentor junior developers" may indicate seniority but should be combined with other evidence rather than triggering alone.

The classifier records: matched phrase, rule identifier, positive/negative signal, and impact on the match band.

## Remote eligibility

Field: `remote_canada_eligibility` — `YES / NO / UNCLEAR`.

- **YES** — explicit Canada-remote language, "open to Canadian applicants," eligible provinces including BC, or a Canadian location with a clearly remote arrangement.
- **NO** — explicit US-only, restricted to an unsupported country/state/province, or legally restricted outside Canada.
- **UNCLEAR** — posting just says "remote" with no geography, conflicting location fields, snippet-only content, or a timezone listed without residency rules.

The word "remote" alone must never produce `YES`.

## Hybrid distance

Haversine distance is simple once coordinates exist — the hard part is resolving location text into coordinates.

**v0 strategy:** a small curated city dictionary (Nanaimo, Parksville, Qualicum Beach, Duncan, Courtenay, Comox, Victoria, Vancouver, Burnaby, Richmond, Surrey, New Westminster), each with city/province/lat/long. Configure the search origin via environment rather than hardcoding it into field names:

```
SEARCH_ORIGIN_NAME=Nanaimo, BC
SEARCH_ORIGIN_LATITUDE=...
SEARCH_ORIGIN_LONGITUDE=...
DEFAULT_HYBRID_RADIUS_KM=...
```

If a posting names a known city, resolve and store distance. If it names an ambiguous region (e.g. "Greater Vancouver," "Vancouver Island," "Nanaimo or Vancouver"), keep the raw text, leave distance null, and mark the location unclear — don't guess unless a rule can safely resolve it. PostGIS and cached geocoding replace this dictionary in v1.

## Classification evidence

A JSON field is sufficient for v0:

```json
{
  "experience": [{"rule_id": "EXP_REQUIRED_RANGE", "text": "1-2 years of software development experience", "type": "required_range", "minimum": 1, "maximum": 2}],
  "seniority": [],
  "remote": [{"rule_id": "REMOTE_CANADA_EXPLICIT", "text": "This role is open to applicants across Canada", "result": "YES"}]
}
```

Plus a readable explanation string, e.g.: "Possible match because the posting requests 1–2 years of experience, explicitly accepts applicants across Canada, and contains no seniority or people-management signals."

This buys immediate trust, easier debugging, a path to user correction, regression fixtures later, and portfolio demonstrations later.

## Interface (Django Admin)

**List columns:** new indicator, match band, title, company, career track, workplace type, remote-Canada eligibility, required/preferred years, distance, posted date, first seen, saved, applied, source.

**Filters:** new, match band, career track, workplace type, remote eligibility, saved, hidden, applied, source, first-seen date, posted date.

**Actions:** mark viewed, save/unsave, hide/unhide, mark/clear applied, open original posting (may need a small custom link column).

**Default review view:**

```sql
hidden_at IS NULL AND applied_at IS NULL
AND match_band IN (MATCH, POSSIBLE, STRETCH, UNCLEAR)
ORDER BY first_seen_at DESC
```

**Rendering source content safely:** classify and display `description_text` by default; never render `description_html_raw` directly, mark content `|safe`, or bypass Django's auto-escaping. If formatted descriptions are added later, sanitize into a separate derived field first.

## Minimum testing (~15–25 tests)

**Experience:** extracts "1+ years," "1–2 years," "2 to 3 years"; separates preferred from required; doesn't treat "experience with Python" as a number; handles missing/conflicting experience language.

**Seniority:** detects Senior/Staff/Principal titles and management roles; doesn't classify "lead a feature" as automatically Lead-level; detects team-management responsibility.

**Remote eligibility:** accepts explicit Canada-remote language, rejects explicit US-only language, keeps unspecified eligibility unclear, handles conflicting location text.

**Import behaviour:** same source job ID doesn't duplicate; changed payload updates the job; unchanged payload preserves `last_changed_at`; reimport preserves saved/applied state; source failure produces a readable error.

## Continuous integration

GitHub Actions: install deps → Ruff lint → Ruff format check → pytest → Django migration check → secret scan (gitleaks) → dependency scan (pip-audit).

CI scanning can catch an accidental secret commit quickly, but it doesn't prevent it from entering Git history — keep `.env` out of Git, use environment variables, optionally add a local pre-commit scan, and rotate any exposed credential immediately.

## Implementation order

1. **Define the exact v0** — this document.
2. **Validate the source** — sample ~30–50 jobs, choose Path A or B, record findings in `docs/source-notes.md`.
3. **Bootstrap the repo** — Django, PostgreSQL, Docker Compose, pytest, Ruff, GitHub Actions, README, `.env.example`.
4. **Add the Job model** — stable source identity, raw payload storage, first/last-seen timestamps, review timestamps, classification fields, unique constraint.
5. **Add the source adapter and import command** — fetch, normalize, hash, upsert, error reporting, idempotency tests.
6. **Add classification modules** — experience, seniority, remote eligibility, career track, match band, explanation, evidence JSON. *(Resolve the career_track/workplace_type gap above before or during this step.)*
7. **Add location handling** — curated coordinates, Haversine distance, unknown-location behaviour, distance display.
8. **Customize Django Admin** — columns, filters, actions, original-posting links, useful default ordering.
9. **Use it for a real week** — record useful jobs, false positives/negatives, wrong extractions, missing filters, repetitive actions, source quality.
10. **Decide v1 priorities using evidence** — don't follow the roadmap blindly; promote features based on real limitations found in step 9.

## Initial GitHub issues

```
1. docs: define the v0 personal utility specification
2. research: validate the first job source
3. chore: initialize Django and PostgreSQL workspace
4. chore: add Docker Compose development environment
5. ci: add backend linting and tests
6. feat(jobs): add the v0 job model
7. feat(ingestion): define the source adapter contract
8. feat(ingestion): import jobs from the first source
9. feat(classification): extract required and preferred experience
10. feat(classification): detect seniority and leadership signals
11. feat(classification): classify remote Canada eligibility
12. feat(classification): add match bands and explanations
13. feat(location): calculate distance for supported cities
14. feat(admin): add the job review dashboard
15. test: cover import idempotency and classifier edge cases
16. docs: record findings from the first week of real use
17. planning: define evidence-based v1 priorities
```

## v0 success metrics

Track: new jobs found per import, relevant jobs found per week, jobs saved/applied to, useful jobs not found as quickly elsewhere, time required for daily review, senior jobs incorrectly shown, realistic jobs incorrectly hidden, remote eligibility mistakes, source that produced each useful lead.

**v0 succeeds when:** it's used for at least one real week, it finds at least one useful lead, reviewing new jobs is faster than checking boards manually, and you want to keep using it.
