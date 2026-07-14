# AGENTS.md

Instructions for Codex and human contributors working in this repository. Keep this file accurate as the project is bootstrapped, especially the commands and repository paths.

## Sources of truth

Before making substantial changes, read the documentation relevant to the task:

* `docs/v0-spec.md` — authoritative requirements for the current v0 milestone
* `docs/vision.md` — product goals and guiding principles
* `docs/roadmap.md` — deferred and future work
* `docs/source-notes.md` — source research, restrictions, and limitations
* `docs/usage-log.md` — findings from real-world use

Use this precedence when instructions differ:

1. The current task
2. `docs/v0-spec.md`
3. Existing accepted implementation and tests
4. `docs/roadmap.md`
5. `docs/vision.md`

This file (`AGENTS.md`) restates a number of `docs/v0-spec.md` rules directly — import idempotency, classification bands, remote eligibility, security baseline — as a convenience, since Codex reads this file every session but only reads `docs/v0-spec.md` when a task calls for it. Where the two differ, `docs/v0-spec.md` is authoritative and this file should be corrected to match it, not the other way around.

Do not implement a roadmap feature merely because it appears in `docs/roadmap.md`.

If requirements materially conflict, report the conflict instead of silently choosing an interpretation.

## Development environment

Django runs on the host and connects to PostgreSQL running through Docker Compose.

Start repository-level services from the repository root:

```powershell
docker compose --env-file app/.env config
docker compose --env-file app/.env up -d
docker compose --env-file app/.env ps
```

Run Python and Django commands from the `app/` directory:

```powershell
cd app
uv sync --locked
uv run python manage.py check
uv run python manage.py migrate
uv run python manage.py runserver
```

When finished, stop PostgreSQL from the repository root without deleting its data volume:

```powershell
cd ..
docker compose --env-file app/.env down
```

## Testing and verification

Run Django checks from the `app/` directory and Compose validation from the repository root:

```powershell
cd app
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
```

```powershell
cd ..
docker compose --env-file app/.env config
```

Ruff, pytest, and CI checks are not yet configured. Add their commands here when that tooling is implemented.

Do not claim that a check passed unless it was actually run successfully.

If a command is not configured, cannot be run, or fails for a pre-existing reason, state that clearly.

## Workflow

Meaningful changes should normally follow:

1. GitHub issue
2. Small feature branch
3. Stated implementation plan
4. Code changes
5. Tests
6. Manual diff review
7. Meaningful commits
8. Pull request
9. Passing CI
10. Merge into `main`

Branch examples:

```text
docs/v0-specification
research/source-validation
chore/bootstrap-django
feat/job-import
feat/experience-classification
feat/remote-eligibility
feat/admin-review
fix/import-idempotency
```

Commit examples:

```text
docs: define v0 job-search workflow
feat(jobs): add source-aware job model
feat(classification): separate required and preferred years
test(ingestion): preserve review state on reimport
ci: run Ruff and pytest
```

Avoid vague commit messages such as:

```text
changes
stuff
working
fix
final
```

The workflow above describes the preferred repository process. Do not create branches, commit, push, merge, rebase, or open pull requests unless explicitly requested.

## Project rules

### Do

* Work on one issue or one clearly bounded task at a time.
* Inspect the repository before making changes.
* Read the documentation relevant to the task.
* Check `git status` before editing.
* Inspect existing implementations before adding or replacing code.
* State a concise plan before substantial or multi-file changes.
* Make the smallest coherent change that satisfies the task.
* Follow existing repository conventions.
* Avoid unrelated refactors.
* Explain why new dependencies are required.
* Add or update tests when behavior changes.
* Update documentation when behavior, setup, or architecture changes.
* Preserve user review state on reimport (see Import rules).
* Review the final diff for unrelated changes.
* Report changed files and their purpose.
* Report the exact verification commands run and their results.
* State what could not be verified.
* Keep source-specific logic inside ingestion adapters.
* Keep classification logic outside management commands.
* Keep shared classification logic independent of individual sources.
* Use deterministic and explainable classification rules.
* Use fixtures, synthetic responses, or mocks for external-source tests.

### Do not

* Build the full roadmap from one prompt.
* Add features deferred by `docs/v0-spec.md`.
* Add Next.js, Celery, Redis, or PostGIS during v0 unless the specification explicitly changes.
* Add multiple job sources during v0 unless explicitly approved.
* Add machine-learning or LLM-based classification during v0.
* Create placeholder infrastructure solely for future features.
* Make unrelated repository-wide formatting changes.
* Upgrade dependencies unless required by the current task.
* Suppress type errors without a documented reason.
* Disable, weaken, or remove tests merely to make a change pass.
* Commit secrets, `.env` files, credentials, personal data, or restricted source content.
* Use live third-party API requests in normal automated tests.
* Invent source permissions, terms, or attribution requirements.
* Scrape LinkedIn or Indeed.
* Bypass CAPTCHAs, access controls, or rate limits.
* Hide failures with broad exception handling.
* Render raw or unsanitized source HTML.
* Replace deterministic classification rules with an unexplained AI call.
* Reset, discard, overwrite, or remove existing user changes.
* Use destructive Git commands unless explicitly instructed.
* Commit, push, merge, rebase, create branches, or open pull requests unless explicitly requested.
* Claim success without running the relevant available verification commands.

## Architecture rules

Breakwater should remain a modular Django monolith during v0.

Keep responsibilities separated:

* `jobs` owns persisted jobs, review state, notes, and admin presentation.
* `ingestion` owns source adapters, fetching, normalization, payload hashing, and import orchestration.
* `classification` owns experience extraction, seniority detection, remote eligibility, career tracks, match bands, evidence, and readable explanations.
* `locations` owns curated location data, normalization, search-origin configuration, and distance calculations.

Management commands should orchestrate application services rather than contain the primary business logic.

Prefer simple functions and cohesive services over unnecessary class hierarchies or speculative abstractions.

## Import rules

Imports must be deterministic and idempotent.

Every imported job must have a non-null and non-blank stable source identifier.

Use a uniqueness constraint equivalent to:

```text
UNIQUE(source_type, source_job_id)
```

If a source does not provide a stable identifier, derive one deterministically from documented stable fields. Never generate a new random identifier on every import.

Reimports must:

* Avoid duplicate rows.
* Update `last_seen_at`.
* Update source-controlled fields when meaningful content changes.
* Update `last_changed_at` only when meaningful content changes.
* Preserve `first_viewed_at`.
* Preserve `saved_at`.
* Preserve `hidden_at`.
* Preserve `applied_at`.
* Preserve `notes`.

Source data must never overwrite owner-controlled review state.

## Classification rules

Classification must initially be deterministic, explainable, testable, and auditable.

Supported match bands are:

```text
MATCH
POSSIBLE
STRETCH
NOT_A_MATCH
UNCLEAR
```

Preserve uncertain opportunities instead of silently hiding them.

Use `UNCLEAR` when evidence is incomplete or conflicting.

Keep required experience separate from preferred experience.

Important classification decisions should store structured evidence and provide a readable explanation.

Remote-Canada eligibility uses:

```text
YES
NO
UNCLEAR
```

The word `remote` alone must never establish Canadian eligibility.

Do not infer legal hiring eligibility solely from a company location or timezone.

Do not publish classification-accuracy claims until they have been measured against labelled data.

## Security and source compliance

Treat all external job content as untrusted.

* Use normalized plain text for classification and default display.
* Never render raw source HTML directly.
* Never mark untrusted source content as safe in Django.
* Never pass unsanitized source content to `dangerouslySetInnerHTML`.
* Use explicit timeouts for outbound requests.
* Use capped retries with backoff only for appropriate transient failures.
* Do not log secrets or complete sensitive source responses without a clear need.
* Use environment variables for secrets.
* Keep `.env` out of Git.
* Keep `.env.example` limited to placeholder values.

If formatted descriptions are introduced later, sanitize them server-side into a separate display-safe field.

If a credential is exposed, report it and recommend immediate rotation or revocation. Do not imply that removing it from Git history alone makes it safe.

## Dependencies

Before adding a dependency:

1. Confirm that the current task requires it.
2. Check whether the standard library or an existing dependency is sufficient.
3. Explain why it is needed.
4. Prefer maintained and widely used packages.
5. Pin or lock it using the repository's established dependency workflow.
6. Update setup documentation when necessary.
7. Add relevant tests.

Do not add infrastructure merely because it may be useful later.

Avoid floating runtime or container tags such as `latest`.

Do not regenerate lockfiles unnecessarily.

## Completion report

At the end of an implementation task, report:

### Summary

What changed and why.

### Changed files

Each changed file and its purpose.

### Tests

Tests added or updated.

### Verification

The exact commands run and their results.

### Not verified

Anything that could not be tested or inspected.

### Notes

Remaining risks, assumptions, migrations, configuration steps, or follow-up work.

Do not report a task complete until the requested work is finished, the relevant available checks have been run, and the final diff has been reviewed.

## Scope

This file applies repository-wide.

If a specific module later needs additional rules that do not apply elsewhere, add a scoped `AGENTS.md` inside that directory rather than continually expanding this root file.

For example, a future frontend under `apps/web/` could have its own `AGENTS.md` with frontend-specific commands and conventions.
