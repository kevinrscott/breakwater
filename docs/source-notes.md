# Breakwater Source Validation

This document records the evidence used to select the first job source for Breakwater v0. It does not establish permission to access, store, or redistribute source content. Facts below come from official documentation; sample findings are observations from public postings retrieved on the review date. Unknowns are not treated as permission.

## Decision

**Status:** Complete for Issue #1

**Decision date:** 2026-07-12

**Selected source and path:** **Lever Postings API, Path B (employer ATS source)**, initially configured with five to ten deliberately selected employer boards.

Lever is the most practical first source because its employer-scoped public feed has the strongest v0 field coverage and the best observed signal for the target search. It supplies a unique posting ID, plaintext description components, ISO country, workplace type, all locations, and separate hosted-posting and application URLs. The sample included a Canada-remote new-graduate software role and other early-career or adjacent roles. This does not make Lever a broad discovery source: usefulness depends on maintaining a small employer registry.

Greenhouse is not selected for the first adapter, not as a future source. Its public API is simple and supplied full descriptions and stable post IDs, but the sampled boards skewed more senior, location was mostly free text, remote-country eligibility was not structured, and the documented GET representation did not expose a separate application URL distinct from the hosted posting URL. Adzuna is not selected for v0 because a credential-free sample was not possible and its documented attribution, access, and termination obligations add avoidable uncertainty for a personal tool and public portfolio demonstration.

## Method and limitations

The task requested approximately 10–20 representative postings per viable candidate.

- **Greenhouse:** 15 current technology postings from the Diligent and Dialpad public boards. The sample was stratified across the two boards after retrieving 118 and 85 open postings respectively, then selecting Canadian/Vancouver technology titles relevant to the target tracks. Visier was checked as a third board, but its four current postings did not supply enough early-career technology roles for the sample.
- **Lever:** 15 current Canadian technology postings, stratified across PolicyMe, PointClickCare, Mechanical Orchard, and ShyftLabs. Their feeds contained 12, 91, 9, and 33 open postings respectively. Selection required `country = CA` and a technology-track title.
- **Adzuna:** 0 postings. The official API requires an `app_id` and `app_key`; no credentials were available and none were created for this research task. It was therefore evaluated as a documented broad-source candidate but not treated as sample-validated.

The samples are purposive, not random or statistically representative. They capture a single day, only a few known employer boards, and no Vancouver Island employer board. “Relevant” means plausibly attainable for an early-career candidate in Nanaimo and either Canada-remote (including BC) or locally practical. Ontario/Toronto hybrid and Vancouver office roles were not counted as relevant. No live application requests were made, no credentials were used, and no complete source payloads were stored in the repository.

## Comparison summary

| Dimension | Greenhouse | Lever | Adzuna |
|---|---|---|---|
| Access and compliance | **CONCERN** — official unauthenticated GET API, but storage/redistribution and third-party portfolio use are not expressly resolved | **CONCERN** — official public-posting API intended for job sites, but storage/redistribution and use by a third-party discovery tool are not expressly resolved | **CONCERN** — documented personal research use, credentials and attribution required; removal obligation on termination |
| Integration feasibility | **PASS** — simple board-scoped GET and optional full content | **PASS** — board-scoped GET, filters and pagination, rich JSON | **CONCERN** — broad search is suitable in shape, but requires registration and has low default quotas |
| v0 field coverage | **CONCERN** — full description and stable ID, but free-text location and no separate application URL | **PASS** — stable ID, plaintext, country, workplace type, all locations, hosted URL, apply URL | **UNKNOWN** — no sample; documentation alone is insufficient |
| Search usefulness | **CONCERN** — 3/15 potentially attainable but none met the full Nanaimo/Canada-remote target | **PASS** — 5/15 potentially attainable; 2/15 met the full target, including one Canada-remote new-grad role | **UNKNOWN** — 0 sampled |
| Import reliability | **CONCERN** — stable IDs; multi-location near-duplicates and board discovery/retirement need handling | **CONCERN** — stable IDs; country-specific sibling posts and missing publication/update timestamps need handling | **UNKNOWN** — not sampled |
| Public portfolio demonstration | **CONCERN** — use synthetic fixtures; do not republish descriptions without resolving employer/Greenhouse rights | **CONCERN** — use synthetic fixtures; public availability is not a redistribution licence | **CONCERN for v0** — mandatory display attribution and termination removal duties complicate a portfolio demo |

## Candidate: Greenhouse

### Confirmed facts

The official [Greenhouse Job Board API documentation](https://developers.greenhouse.io/job-board.html) says Job Board data is public and GET endpoints require no authentication. `GET /v1/boards/{board_token}/jobs` returns published posts; `content=true` adds the full post description, departments, and offices. Greenhouse identifies `id` as the unique job-post identifier and also exposes `internal_job_id`, `updated_at`, free-text `location.name`, and `absolute_url`. A single-job response can expose `first_published`. Application submission is a separate authenticated POST operation; the documented GET representation does not define a separate application URL.

The documentation does not state a GET rate limit, attribution rule, retention period, or licence for a third party to store and redistribute employer descriptions. Greenhouse’s customer agreement is not evidence that Breakwater, which is not the customer publishing the board, has those rights.

### Observed sample findings

- **Sample:** 15 postings on 2026-07-12; Diligent and Dialpad Canadian/Vancouver technology roles.
- **Relevant-job yield:** 3/15 (20%) potentially attainable under the experience bands; 0/15 met the full Nanaimo/Canada-remote-or-nearby target. Vancouver office roles are not a practical Nanaimo commute.
- **Description coverage:** `FULL` 15, `PARTIAL` 0, `SNIPPET` 0, `UNKNOWN` 0. Content was HTML/entity encoded and must be converted to normalized plain text before classification or display.
- **Experience/seniority:** numeric wording was usually clear (examples in the sample included 1–3, 2–3, 2–4, 3–5, 4+, 5+, 7+, and 10+ years). Most sampled roles were mid-level or senior; a few Software Engineer II/Solutions Engineer roles fell into possible or stretch territory.
- **Location/remote detail:** locations were readable but free text. No structured country or workplace field was present in the documented job representation. Office wording in descriptions helped, but “Vancouver, Canada” did not establish a remote arrangement.
- **URLs and identity:** all 15 had nonblank unique `id` and `absolute_url` values. `absolute_url` was the original hosted posting. A distinct application URL was not returned.
- **Duplicates:** 0 repeated IDs and 0 repeated `absolute_url` values. Two title/description pairs appeared to be the same role published separately for Kitchener and Vancouver with different post IDs; treat these as suspected multi-location siblings, not exact duplicates.
- **Likely failures:** retired board tokens or jobs returning 404, one board failing while others remain healthy, HTML/entity normalization changes altering hashes, employer-edited locations, separate posts for each location, and `updated_at` changes that do not represent meaningful job-content changes.

### Assumptions and unresolved questions

- It is an assumption that periodic low-volume personal GET polling is acceptable merely because GET data is public; public access is not by itself a storage or redistribution licence.
- No additional permission work is required for the intended personal, low volume v0 scope. Reassess source terms only if the project's usage distribution, or collection volume changes substantially.
- Confirm whether locally retained full descriptions/raw payloads are permitted and how quickly expired content should be removed.
- Confirm whether a public portfolio may show live employer content or Greenhouse branding. Until resolved, use synthetic fixtures and link to the original posting only.

### Assessment

Greenhouse is technically easy and a credible fallback. It is not selected because the sampled target yield was weaker and its schema leaves more remote-eligibility and application-link work to description parsing.

## Candidate: Lever

### Confirmed facts

The official [Lever Postings API repository](https://github.com/lever/postings-api) describes the API as a way to create a job site and states that published postings are publicly viewable. `GET /v0/postings/{site}` supports `skip`, `limit`, and employer-defined filters. Its JSON fields include a unique posting `id`, title, primary and all locations, ISO 3166-1 alpha-2 `country` (or null), plaintext and HTML description components, `hostedUrl`, `applyUrl`, and `workplaceType` (`unspecified`, `on-site`, `remote`, or `hybrid`). The list/single-post GET examples do not require an API key; a key and documented rate limiting apply to application POSTs, which Breakwater will not use.

The official documentation does not specify a GET request limit, attribution requirement, retention period, publication timestamp, update timestamp, or an express licence for storage/redistribution by an independent job-discovery tool.

### Observed sample findings

- **Sample:** 15 postings on 2026-07-12; PolicyMe (4), PointClickCare (4), Mechanical Orchard (4), and ShyftLabs (3).
- **Relevant-job yield:** 5/15 (33%) potentially attainable. 2/15 (13%) met the full target: Mechanical Orchard’s “Software Engineer [New Grads Welcome]” was Canada-remote, and a Canada-remote adjacent implementation role was within the stretch range. Other promising junior/associate roles were Ontario/Toronto hybrid or Ontario-scoped remote and therefore not assumed open to BC.
- **Description coverage:** `FULL` 15, `PARTIAL` 0, `SNIPPET` 0, `UNKNOWN` 0 when `descriptionPlain`, `lists[].content`, and `additionalPlain` were combined. Looking only at `descriptionPlain` would have falsely marked some records incomplete.
- **Experience/seniority:** wording included junior, associate/new-grad, 1–4 preferred, 2 years including co-op/internships, 2–4, 5+, 7+, and 10+ years. This was useful for testing required/preferred separation and equivalent-experience handling.
- **Location/remote detail:** all 15 exposed `country = CA`; 9 were marked remote and 6 hybrid. The structured country/workplace combination was materially better than Greenhouse, but employer-entered inconsistencies existed (for example, “Remote or Mississauga” paired with `hybrid`). Ontario location plus `remote` was not treated as BC eligibility.
- **URLs and identity:** all 15 had unique UUID-like `id`, `hostedUrl`, and `applyUrl` values. Hosted and application URLs were distinct and direct to the employer’s Lever board.
- **Duplicates:** 0 repeated IDs, hosted URLs, or apply URLs. The wider board inspection showed Canada/US sibling postings for the same title with separate IDs; source identity alone should preserve both, while country filters prevent the US sibling from entering the v0 queue.
- **Likely failures:** board-name changes or EU/global instance mismatch, per-board 404s, null/incorrect `country`, contradictory workplace/location fields, description content spread across several fields, expired posts disappearing without tombstones, no source publication/update timestamp, and multi-country sibling postings.

### Assumptions and unresolved questions

- The successful unauthenticated GETs and public-posting documentation support technical access, but do not prove permission for indefinite local retention or redistribution.
- Confirm acceptable GET polling frequency and third-party use with Lever or each selected employer before moving beyond low-volume personal use.
- Confirm whether expired descriptions/raw payloads must be deleted and whether a public demo may show live content. Until resolved, keep the portfolio demo synthetic and preserve original links/clear employer attribution in personal use.
- Verify whether posting IDs remain stable when an employer edits, unpublishes, and republishes a role; treat a new ID as a new source record unless evidence supports an alias.

### Assessment

Lever is selected. It offers the strongest deterministic inputs for remote-country classification and the cleanest route back to the application. Its employer-scoped coverage is the principal weakness, addressed in Path B by a small curated `EmployerSource` registry and per-board failure isolation.

## Candidate: Adzuna (broad discovery)

### Confirmed facts

The official [Adzuna API overview](https://developer.adzuna.com/overview) describes a REST API with job-ad search endpoints and requires registration for an `app_id` and `app_key`. The official [API terms of service](https://developer.adzuna.com/docs/terms_of_service) permit publishing Adzuna listings and personal research, subject to Adzuna’s discretion. Default access is 25 requests/minute, 250/day, 1,000/week, and 2,500/month. Published adverts require “Jobs by Adzuna” branding/linking; published research must acknowledge and link to Adzuna. On termination, acquired data must be removed from website pages. The terms also restrict contacting third-party content providers and commercial reuse.

### Observed sample findings

- **Sample:** 0 postings. Authentication credentials were unavailable, so description completeness, stable IDs, destination URLs, Canadian remote detail, duplicate rates, and relevant yield were not observed.
- A documentation-only schema review is not a substitute for the requested posting sample. Adzuna is therefore not validated as viable for v0.

### Assumptions and unresolved questions

- It is plausible, but unverified here, that a broad aggregator would improve employer coverage.
- Registration approval, Canadian early-career yield, full-description availability, original-employer URL quality, stable identity, and duplicate behavior remain unresolved.
- The terms do not clearly answer Breakwater’s proposed local raw-payload retention. Written clarification would be needed before relying on indefinite retention or a public demo.

### Assessment

Adzuna is a credible documented broad candidate, but it is not selected for the first source. The missing sample prevents a utility decision, and its attribution/removal obligations are more complex than the selected ATS path.

## Important risks accepted by the decision

- **Coverage risk:** Lever has no cross-employer search. A weak employer list will miss useful jobs.
- **Permission risk:** public technical access does not conclusively resolve storage, retention, redistribution, or portfolio-display rights.
- **Freshness risk:** the feed does not document published/updated timestamps, so `posted_at` may remain null and meaningful changes must be detected by normalized payload hashing.
- **Eligibility risk:** `country = CA` plus `workplaceType = remote` is strong source evidence but employer-entered text can narrow eligibility to a province; classification must preserve conflicts as `UNCLEAR`.
- **Duplicate risk:** employers may publish country/location siblings with different IDs. v0 identity remains `(source_type, source_job_id)`; similarity deduplication stays out of scope.
- **Operational risk:** each employer board can disappear, move to the EU instance, rename, or return malformed content independently.

## Source-dependent changes needed later in `docs/v0-spec.md`

Do not edit the specification as part of this issue. A later documentation change should:

1. Name Lever Postings API as the v0 source and select Path B.
2. Require `EmployerSource` with Lever site name, API instance (`global` or `EU`), careers URL, active state, and per-board success/failure tracking.
3. Define `source_job_id` as Lever’s posting `id`; do not invent a fallback unless a future observed payload lacks it.
4. Map `hostedUrl` to `source_url`, `applyUrl` to `application_url`, `country`/`categories.allLocations` to normalized location evidence, and `workplaceType` to workplace evidence.
5. Define description normalization across `descriptionPlain`, `lists[].content` converted to plain text, and `additionalPlain`; keep source HTML unrendered.
6. Allow `posted_at` to be null because the Postings API does not document publication/update timestamps; use first-seen time separately.
7. Configure five to ten Lever employer sites and isolate request/normalization failures per board, including global/EU base URL configuration.
8. Document conservative polling, explicit timeouts, capped retries, 404/retired-board handling, and an `UNKNOWN` GET-rate-limit assumption pending confirmation.
9. State that live source descriptions/raw payloads are for low-volume personal use only until retention and redistribution rights are clarified; public portfolio fixtures must be synthetic.

## Authoritative sources reviewed

- [Greenhouse Job Board API](https://developers.greenhouse.io/job-board.html) — access, authentication, endpoints, fields, identifiers, and full-content option; reviewed 2026-07-12.
- [Lever Postings API](https://github.com/lever/postings-api) — intended use, endpoints, filters, fields, public posting behavior, URLs, country/workplace data, and application-only rate limit; reviewed 2026-07-12.
- [Adzuna API overview](https://developer.adzuna.com/overview) — authentication and API shape; reviewed 2026-07-12.
- [Adzuna API terms of service](https://developer.adzuna.com/docs/terms_of_service) — permissible use, quotas, attribution, termination, and reuse restrictions; reviewed 2026-07-12.
