# Roadmap — v1 and Beyond

This is where Breakwater goes *after* v0 is validated by real use. Nothing here is a commitment — v0's Step 10 is "decide v1 priorities using evidence," not "work through this list in order." Rough time-boxes are evenings/weekends estimates, not deadlines.

## v1 additions to the stack

Add only when needed: Django REST Framework, django-filter, Next.js, TypeScript, Tailwind CSS, Zod, Playwright, PostGIS, TanStack Query, React Hook Form, Pyright/mypy, Redis, Celery, Celery Beat, pgvector, S3-compatible storage, error monitoring.

## B1 — Improve classification *(~1–2 weeks)*

Richer evidence spans, confidence scores, a user-correction workflow, regression fixtures, and evaluation-guided rule improvements — plus separate classification models if justified by then.

**Done when:** corrected mistakes become tests, evaluation guides rule changes, and confidence or evidence improvements make ambiguous results easier to review without weakening deterministic explanations.

## B2 — Add a second source *(~1–2 weeks)*

One additional ATS adapter, extension of the existing shared adapter contract for multiple sources, and support for multiple source records per normalized job if needed.

**Done when:** both adapters share tested normalization and import contracts, reimports stay idempotent, and direct employer links are still preferred.

## B3 — Build the Next.js frontend *(~1–2 weeks)*

Next.js, TypeScript, Tailwind, Django REST Framework, a search dashboard, job cards and detail view, URL-based filters, save/hide/applied actions, responsive layout.

**Done when:** the Django Admin workflow is fully represented, search URLs are shareable, loading/empty/error states exist, and job descriptions render as safe text/markdown — never `dangerouslySetInnerHTML` on raw source data.

## B4 — Upgrade location with PostGIS *(~3–5 days)*

PostGIS, structured locations, configurable radius, a geocoding cache with confidence scores, radius queries.

**Done when:** remote-Canada plus hybrid-radius works reliably, ambiguous locations stay explicit, and low-confidence geocodes never silently determine eligibility.

## B5 — Evaluation and deduplication *(~1 week)*

A labelled fixture dataset, an evaluation command, published metrics, similarity-based duplicate candidates, preferred-source selection, incorrect-merge correction.

**Measure:** senior-job leakage, valid early-career recall, required/preferred-years accuracy, remote eligibility accuracy, role-family accuracy, duplicate precision.

## B6 — Additional sources and scheduling *(~1–2 weeks)*

Additional source adapters beyond B2 (for example, Ashby), Redis + Celery, scheduled imports, scheduling-specific retry policies, duplicate-task prevention, and failed-task visibility. Only add Celery/Redis once manual imports are genuinely inconvenient.

## B7 — Deployment and portfolio polish *(~1–2 weeks)*

**Production configuration:** `SECRET_KEY` from a platform secret store, `DEBUG = False`, explicit `ALLOWED_HOSTS`, HTTPS enforced, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, explicit `CSRF_TRUSTED_ORIGINS`, HSTS after HTTPS is verified, correct proxy SSL headers for the hosting platform, and logs reviewed for leaked secrets or sensitive API responses.

**Plus:** public frontend, hosted API and PostgreSQL, synthetic/approved demo data, an architecture diagram, a demo video, a complete README, ADRs written for decisions actually made along the way (not pre-drafted), known limitations, error monitoring, and a portfolio case study.

**Done when:** the public demo works, CI (including secret/dependency scans) passes, setup works from a clean clone, no personal data or restricted source content is exposed, evaluation claims are backed by real results, and the production checklist above is satisfied.

## Optional stretch work (only after B7)

Structured candidate profile, full application tracker, saved searches, alerts, resume PDF/DOCX extraction, pgvector, semantic search, LLM-assisted ambiguity review, multiple users, email notifications, object storage.

Resume matching specifically is not required for the project to be valuable or portfolio-worthy — it's fine if it never happens.

## v1 success metrics

Public demo works; README explains the problem clearly; classifier metrics are published; multiple adapters share a tested contract; PostGIS supports a real workflow; deduplication is demonstrated; scheduled-import failures are visible; CI passes; setup works from a clean clone; no personal information or secrets are committed; the project has meaningful issue and PR history.

## README, once v1 exists

Suggested structure for the public-facing README at that point: problem → product demonstration → what Breakwater does differently → architecture → data-source strategy → explainable classification → remote/hybrid eligibility → evaluation results → local setup → testing and CI → privacy and source compliance → known limitations → future work.
