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
  -> Jobs, curated employer sources, review state, raw source payloads
```

v0 is a modular monolith — simple doesn't mean everything lives in one management command.

## Repository structure

```
breakwater/
├── app/
│   ├── config/
│   ├── jobs/                   (models.py, management/commands/import_jobs.py)
│   ├── ingestion/              (adapters/, normalization.py, services.py, types.py, tests/)
│   ├── classification/         (experience.py, seniority.py, types.py, tests/)
│   ├── .env.example
│   ├── manage.py
│   ├── pyproject.toml
│   └── uv.lock
├── docs/
├── .github/workflows/backend.yml
├── compose.yaml
├── AGENTS.md
└── README.md
```

Location handling remains planned v0 work. When implemented, it should follow the same direct package layout under `app/` (for example, `app/locations/`), rather than introducing an `app/breakwater/` package.

Don't create `apps/web` until the frontend actually exists.

## Source selection

v0 uses the **Lever Postings API through Path B (employer ATS source)**. Configure five to ten deliberately selected employer boards through the curated `EmployerSource` registry. The validation evidence, limitations, and compliance caveats behind this accepted decision remain in [`source-notes.md`](source-notes.md).

Lever posting `id` is the required `source_job_id`; `hostedUrl` maps to `source_url`, and `applyUrl` maps to `application_url`. Normalize location from `categories.allLocations` (falling back to the primary location), preserve `country` and `workplaceType` as classification evidence, and build `description_text` from `descriptionPlain`, `lists[].content` converted to plain text, and `additionalPlain`. Because Lever does not document publication or update timestamps, `posted_at` may be null and remains distinct from first-seen time.

Support Lever's global and EU API instances and isolate request or normalization failures per employer board so one board does not block the rest. Poll conservatively with the outbound-request safeguards above; the GET rate limit is unknown. Live descriptions and raw payloads remain limited to low-volume personal use until retention and redistribution rights are clarified, and any public portfolio fixtures must be synthetic.

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

### EmployerSource

```
id, company_name, source_type, api_instance, board_identifier, careers_url,
is_active, last_import_at, last_success_at, consecutive_failures,
notes, created_at, updated_at
```

Use `api_instance = global / eu` for Lever and keep `(source_type, api_instance, board_identifier)` unique.

## Ingestion design

The management command orchestrates the import; it doesn't contain the business logic.

**Flow:** fetch raw jobs → validate source fields → normalize → calculate payload hash → classify career track and role family → classify workplace type → classify experience and seniority → classify remote eligibility or resolve location and distance as applicable → determine match band → build explanation and evidence → upsert on `source_type + source_job_id` → set first_seen/last_seen/last_changed.

**Adapter contract:**

```python
class JobSourceAdapter(Protocol):
    source_name: str
    def fetch_jobs(self) -> Iterable[RawJob]: ...
    def normalize_job(self, raw_job: RawJob) -> NormalizedJobInput: ...
```

Even with one adapter in v0, this contract keeps the management command from becoming source-specific. `fetch_jobs` applies an explicit timeout and a capped retry-with-backoff policy; a failed single-source import terminates with a clear error rather than hanging. Multi-board ATS adapters isolate failures per board.

**Idempotent reimports:** create on new source ID, update `last_seen_at` on existing, update source-controlled fields only when the payload hash changes, set `last_changed_at` only on meaningful source-controlled content changes, and never overwrite user notes or reset saved/hidden/viewed/applied state.

**Version-aware reclassification:** reclassify an existing job whenever its stored `classifier_version` differs from the current classifier version, even when its source payload hash is unchanged. A missing or null stored version counts as different. A classifier-only update may refresh derived classification fields, evidence, and explanation, but must not update `last_changed_at`; that timestamp remains tied to meaningful source-controlled content changes. Reclassification must preserve all owner-controlled review state.

**Atomic classification persistence:** persist all derived classification fields, evidence, explanation, and `classifier_version` as one complete result. Store the new classifier version only after the entire classification run succeeds. If classification fails, retain the prior complete classification result rather than combining fields produced by different classifier versions.

## Classification contract

Classification is deterministic, explainable, testable, and auditable. It produces career, workplace, geographic eligibility, experience, seniority, and match results in one versioned run. Missing or contradictory critical evidence is preserved as `UNCLEAR` rather than guessed or silently excluded.

### Career track and role family

Career tracks are:

```text
PRIMARY_DEVELOPMENT
ADJACENT_TECHNOLOGY
INTERIM
OUT_OF_SCOPE
UNCLEAR
```

Role families are:

```text
SOFTWARE_DEVELOPMENT
QA_AUTOMATION
APPLICATION_SUPPORT
TECHNICAL_SUPPORT
IMPLEMENTATION
IT_SYSTEMS
ADMINISTRATION
CUSTOMER_SUPPORT
DATA_OPERATIONS
TECHNICAL_WRITING
OTHER
UNCLEAR
```

The normal role-family-to-track mapping is:

| Career track | Role families |
|---|---|
| `PRIMARY_DEVELOPMENT` | `SOFTWARE_DEVELOPMENT` |
| `ADJACENT_TECHNOLOGY` | `QA_AUTOMATION`, `APPLICATION_SUPPORT`, `TECHNICAL_SUPPORT`, `IMPLEMENTATION`, `IT_SYSTEMS` |
| `INTERIM` | `ADMINISTRATION`, `CUSTOMER_SUPPORT`, `DATA_OPERATIONS`, `TECHNICAL_WRITING` |
| `OUT_OF_SCOPE` | `OTHER` |
| `UNCLEAR` | `UNCLEAR` |

For v0, `SOFTWARE_DEVELOPMENT` includes backend, frontend, full-stack, web, WordPress, Python, and integration-development roles. Do not create a more granular or exhaustive taxonomy yet.

Use the title as the primary evidence for career track and role family. Responsibilities may resolve an ambiguous title, but incidental technology, industry, or skill mentions do not determine the family.

When two or more role families remain equally plausible, set `role_family = UNCLEAR`. Preserve the career track when every plausible family maps to the same track; for example, a role that could be either `APPLICATION_SUPPORT` or `TECHNICAL_SUPPORT` may be `career_track = ADJACENT_TECHNOLOGY` and `role_family = UNCLEAR`. Set `career_track = UNCLEAR` only when the plausible families cross career-track boundaries.

`OTHER / OUT_OF_SCOPE` means the role is understood confidently but falls outside the supported v0 role families. `UNCLEAR / UNCLEAR` means the role itself cannot be identified confidently because evidence is missing, ambiguous, or contradictory. Never use `OTHER` as a fallback for uncertainty.

Career track and match band are separate decisions. For example, an attainable administrative job may be `INTERIM` and `MATCH`; the interface and explanation must not present it as equivalent to a `PRIMARY_DEVELOPMENT` match.

`role_family = UNCLEAR` does not automatically force `match_band = UNCLEAR` when the career track is known and finer role-family precision is unnecessary for the match decision. `career_track = UNCLEAR` is critical career uncertainty and does force an unclear match unless a hard exclusion already applies.

### Workplace and geographic eligibility

Workplace types are:

```text
REMOTE
HYBRID
ON_SITE
UNCLEAR
```

Use structured source workplace evidence when it is reliable. Missing or `unspecified` structured evidence remains `UNCLEAR` unless explicit posting text resolves it. A generic workplace mention is not necessarily a conflict; when reliable posting-level workplace metadata and explicit posting text directly conflict, return `UNCLEAR` unless one source can safely be treated as generic, stale, or less authoritative.

Workplace type must be sufficiently resolved before applying a geographic eligibility path. `REMOTE` jobs require remote-Canada eligibility evidence. `HYBRID` and `ON_SITE` jobs require location and distance evidence. Missing evidence from a geographic category that does not apply to the resolved workplace type does not produce `UNCLEAR`.

`REMOTE` jobs use `remote_canada_eligibility`:

```text
YES
NO
UNCLEAR
```

- **YES** — explicit Canada-remote language, "open to Canadian applicants," eligible provinces including BC, or reliable posting-level country, residency, province, or eligibility metadata paired with a clearly remote arrangement and no narrower conflicting restriction.
- **NO** — explicit US-only language, restriction to an unsupported country/state/province, or a legal residency restriction outside Canada.
- **UNCLEAR** — "remote" without eligible geography, unresolved authoritative eligibility conflicts, incomplete applicable evidence, or a timezone without residency rules.

Reliable posting-level country, residency, province, or eligibility metadata may contribute to remote-Canada eligibility. Company headquarters, company country, office location, and timezone alone do not establish applicant eligibility. The word "remote" alone must never establish Canadian eligibility.

Explicit posting restrictions override generic or permissive metadata. For example, generic remote metadata paired with "Applicants must reside in the United States" produces `NO`. When authoritative posting-level structured evidence and explicit posting text directly conflict, and neither can safely be treated as generic, stale, or less authoritative, return `UNCLEAR`; authoritative Canadian eligibility metadata conflicting with equally authoritative residency text is one such case.

`HYBRID` and `ON_SITE` jobs use resolved location and distance from the configured search origin. Resolve coordinates only from the curated v0 location data; never guess coordinates. If the location is ambiguous or cannot be resolved with the curated dictionary, preserve its text, leave coordinates and distance null, and treat location as `UNCLEAR` for matching. Absence from the dictionary alone is not proof that a location is unsupported.

A location is a hard exclusion only when available evidence establishes that it is outside the supported geography or configured radius. A clearly identified Toronto on-site role may therefore be excluded, while an unresolved Ladysmith role remains `UNCLEAR` solely because the v0 dictionary cannot resolve it. Do not add guessed coordinates to force a decision.

Haversine distance is simple once coordinates exist. The v0 curated city dictionary contains Nanaimo, Parksville, Qualicum Beach, Duncan, Courtenay, Comox, Victoria, Vancouver, Burnaby, Richmond, Surrey, and New Westminster, each with city, province, latitude, and longitude. Configure the search origin rather than hardcoding it into field names:

```text
SEARCH_ORIGIN_NAME=Nanaimo, BC
SEARCH_ORIGIN_LATITUDE=...
SEARCH_ORIGIN_LONGITUDE=...
DEFAULT_HYBRID_RADIUS_KM=...
```

PostGIS and cached geocoding remain v1 work.

### Experience and seniority

Store required and preferred experience separately: `years_required_min`, `years_required_max`, `years_preferred`, and `experience_requirement_type` (`REQUIRED / PREFERRED / NICE_TO_HAVE / FLEXIBLE / AMBIGUOUS / NOT_FOUND`).

Examples: "1+ years required" → `required_min = 1`. "1–2 years of professional experience" → `required_min = 1, required_max = 2`. "2 years preferred" → `preferred = 2, type = PREFERRED`. "Experience with Python" → no numeric requirement. "5 years of combined education and experience" must **not** automatically become five professional years.

Strong seniority evidence includes senior, staff, principal, lead engineer, architect, manager, director, head of, "manage a team," "performance management," "hire engineers," "set organization-wide strategy," and "own engineering standards."

Seniority evidence must be contextual. "Lead a small feature" is not automatically Lead-level; "Lead Engineer" is a strong signal; and "mentor junior developers" may indicate seniority but needs other supporting evidence rather than triggering a hard exclusion alone.

### Match-band precedence

Evaluate match bands in this order so overlapping evidence has one deterministic outcome.

First apply hard exclusions. Any of the following produces `NOT_A_MATCH`:

- the supported career track is `OUT_OF_SCOPE`;
- strong senior, staff, principal, architect, management, hiring, or organization-wide ownership evidence;
- a required minimum of four or more years;
- a `REMOTE` job has `remote_canada_eligibility = NO`; or
- available evidence establishes that a `HYBRID` or `ON_SITE` location is outside the supported geography or configured radius.

When no hard exclusion applies, return `UNCLEAR` if critical career, experience, workplace, or the applicable geographic evidence is incomplete or contradictory. Remote eligibility is applicable to `REMOTE`; location and distance are applicable to `HYBRID` and `ON_SITE`. Missing evidence from an inapplicable category does not affect the band. The absence of a numeric experience requirement is not itself incomplete when the available content has been reviewed and no numeric requirement is found. `UNCLEAR` stays reviewable.

Required numeric experience produces these mutually exclusive outcomes:

- **MATCH** — an exact or bounded required maximum of no more than one year.
- **POSSIBLE** — an exact or bounded required maximum greater than one and no more than two years, or `1+ years` required.
- **STRETCH** — `2+ years` required; `3+ years` required; exactly three years required; or a bounded required range extending beyond two years while its minimum remains below four.
- **NOT_A_MATCH** — a required minimum of four or more years, including `4 years`, `4+ years`, or a range such as `5–7 years`.

A bounded range such as `1–4 years` is `STRETCH`, not automatically a four-year-minimum `NOT_A_MATCH`. Required and preferred experience remain separate. Four or more years preferred, but not required, may produce `STRETCH` rather than `NOT_A_MATCH`. When there is no numeric requirement, explicit junior, entry-level, new-graduate, associate, trainee, or internship language produces `MATCH`; flexible equivalent-experience wording, up to three years preferred, or an otherwise clear supported non-senior role produces `POSSIBLE`.

Hard exclusions take precedence over positive language: for example, a posting labelled "junior" with a required minimum of four years remains `NOT_A_MATCH`.

### Evidence, explanations, and versioning

`classification_evidence` has these category keys:

```text
career
experience
seniority
workplace
remote
location
match
```

Each evidence entry uses a stable `rule_id`, names the relevant normalized or persisted `source_field`, and includes only a short relevant `excerpt` when source text is needed. Store structured values as separately typed fields rather than encoding multiple or numeric values into a string. A single `result` field remains appropriate for an individual outcome such as `REMOTE`, `YES`, `MATCH`, or `UNCLEAR`. Do not copy complete descriptions into evidence. Empty categories are stored as empty arrays so a complete run has a consistent shape.

One concise illustrative record:

```json
{
  "career": [{"rule_id": "CAREER_TITLE_SOFTWARE", "source_field": "title", "excerpt": "Junior Software Developer", "career_track": "PRIMARY_DEVELOPMENT", "role_family": "SOFTWARE_DEVELOPMENT"}],
  "experience": [{"rule_id": "EXP_REQUIRED_EXACT", "source_field": "description_text", "excerpt": "1 year of development experience", "requirement_type": "REQUIRED", "minimum": 1, "maximum": 1}],
  "seniority": [],
  "workplace": [{"rule_id": "WORKPLACE_STRUCTURED_REMOTE", "source_field": "workplace_evidence", "result": "REMOTE"}],
  "remote": [{"rule_id": "REMOTE_CANADA_EXPLICIT", "source_field": "description_text", "excerpt": "open to applicants across Canada", "result": "YES"}],
  "location": [],
  "match": [{"rule_id": "MATCH_MAX_ONE_YEAR", "source_field": "years_required_max", "result": "MATCH"}]
}
```

When `content_completeness` affects the final band, record the reason in the `match` category rather than adding another evidence category:

```json
{"rule_id": "MATCH_PARTIAL_CONTENT", "source_field": "content_completeness", "result": "UNCLEAR"}
```

`classification_explanation` is a concise readable summary of the decisive evidence, not a dump of every match. Example: "Primary-development match: the title is Junior Software Developer, the posting requires one year of experience, and the remote role is explicitly open across Canada."

`classifier_version` identifies the complete classification run, beginning with `v0.1`. It covers all career, experience, seniority, workplace, remote, location, match, evidence, and explanation rules; do not version components independently in v0. Change the version whenever a rule change can alter persisted classification output. The version-aware reclassification and atomic-persistence rules in the ingestion contract apply whenever that version changes.

This evidence contract buys immediate trust, easier debugging, a path to user correction, regression fixtures later, and portfolio demonstrations later.

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
2. **Validate the source** — completed: Lever Postings API / Path B was selected and the evidence was recorded in `docs/source-notes.md`.
3. **Bootstrap the repo** — Django, PostgreSQL, Docker Compose, pytest, Ruff, GitHub Actions, README, `.env.example`.
4. **Add the Job model** — stable source identity, raw payload storage, first/last-seen timestamps, review timestamps, classification fields, unique constraint.
5. **Add the source adapter and import command** — fetch, normalize, hash, upsert, error reporting, idempotency tests.
6. **Add classification modules** — experience, seniority, remote eligibility, career track, role family, workplace type, match band, explanation, evidence JSON, and classifier version.
7. **Add location handling** — curated coordinates, Haversine distance, unknown-location behaviour, distance display.
8. **Customize Django Admin** — columns, filters, actions, original-posting links, useful default ordering.
9. **Use it for a real week** — record useful jobs, false positives/negatives, wrong extractions, missing filters, repetitive actions, source quality.
10. **Decide v1 priorities using evidence** — don't follow the roadmap blindly; promote features based on real limitations found in step 9.

## Implementation tracking

The repository's actual issue and pull-request history now tracks implementation. Do not use this specification as a duplicate issue backlog; create small, current issues from the remaining v0 requirements as needed.

## v0 success metrics

Track: new jobs found per import, relevant jobs found per week, jobs saved/applied to, useful jobs not found as quickly elsewhere, time required for daily review, senior jobs incorrectly shown, realistic jobs incorrectly hidden, remote eligibility mistakes, source that produced each useful lead.

**v0 succeeds when:** it's used for at least one real week, it finds at least one useful lead, reviewing new jobs is faster than checking boards manually, and you want to keep using it.
