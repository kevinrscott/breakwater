# Breakwater Source Validation

This document is the evidence record for selecting the first job-data source used by Breakwater v0. It does not establish permission to access, store, or redistribute source content. Claims must be supported by official documentation, observed samples, or clearly labelled assumptions.

## Decision status and summary

**Status:** Not started

**Summary:** No source has been selected. Greenhouse, Lever, and one credible broad job-discovery source will be evaluated before importer implementation begins.

## Evaluation rubric

Record each dimension as `PASS`, `CONCERN`, `FAIL`, or `UNKNOWN`, with a short explanation and an evidence reference. `UNKNOWN` is not evidence of permission or suitability.

| Dimension | Evidence to record |
|---|---|
| Access and compliance | Official documentation, permitted access method, terms, restrictions, attribution, and review date |
| Integration feasibility | Authentication, request method, constraints, timeouts, pagination, and stable identifiers |
| v0 field coverage | Original and application URLs, title, company, description completeness, dates, location, and remote-country detail |
| Search usefulness | Representative sample size, relevant-job yield, experience wording, location quality, and source coverage |
| Import reliability | Duplicate behaviour, update semantics, unavailable records, malformed responses, and other failure modes |
| Data handling | Storage, retention, redistribution, public-demo, and raw-content restrictions |

A candidate recommendation must distinguish confirmed facts from assumptions. The final decision should explain why the selected candidate is preferable for v0 and identify any unresolved condition that must be addressed before implementation.

## Representative sample method

For each candidate, inspect approximately 30–50 representative postings where possible, following `docs/v0-spec.md`. Record the actual sample size, date, search inputs or employer boards, and any sampling limitations. Do not store credentials, restricted source content, or personal data in this repository.

Use the following measures consistently:

- **Relevant-job yield:** relevant postings divided by the total representative sample, with relevance judged against the current v0 target profile.
- **Description coverage:** counts of `FULL`, `PARTIAL`, `SNIPPET`, and `UNKNOWN` content.
- **Duplicate behaviour:** exact repeated source identifiers, repeated application URLs, and suspected cross-postings reported separately.

## Candidate: Greenhouse

### Decision status and summary

**Status:** Not evaluated

**Summary:** Candidate retained for evidence-based evaluation. No conclusion has been reached about access, suitability, or support for Breakwater's intended use.

### Candidate overview

| Topic | Findings |
|---|---|
| Official documentation | Not yet recorded or verified |
| Confirmed facts | None recorded |
| Assumptions and open questions | Identify the relevant product or endpoint; verify access conditions, coverage, and whether multiple employer boards can be evaluated consistently |
| Integration method | Unknown |
| Authentication | Unknown |
| Terms and access restrictions | Unknown; must be reviewed from authoritative sources |
| Attribution requirements | Unknown |
| Rate limits or request constraints | Unknown |
| Storage, retention, and redistribution | Unknown; assess raw payloads, descriptions, local retention, and public-demo use separately |

### Field coverage

| Field or capability | Result | Evidence or notes |
|---|---|---|
| Stable job identifier | UNKNOWN | Not evaluated |
| Original posting URL | UNKNOWN | Not evaluated |
| Application URL | UNKNOWN | Not evaluated |
| Full description | UNKNOWN | Not evaluated |
| Publication or update date | UNKNOWN | Not evaluated |
| Location detail | UNKNOWN | Not evaluated |
| Remote-country eligibility detail | UNKNOWN | Not evaluated |
| Experience wording | UNKNOWN | Not evaluated |

### Representative sample findings

- **Sample date and size:** Not sampled
- **Search inputs or employer boards:** Not selected
- **Relevant-job yield:** Unknown
- **Description coverage:** Unknown
- **Duplicate behaviour:** Unknown
- **Failure modes:** Unknown

### Assessment

- **Advantages:** Not established
- **Risks and disadvantages:** Not established
- **Candidate recommendation:** Pending evidence

## Candidate: Lever

### Decision status and summary

**Status:** Not evaluated

**Summary:** Candidate retained for evidence-based evaluation. No conclusion has been reached about access, suitability, or support for Breakwater's intended use.

### Candidate overview

| Topic | Findings |
|---|---|
| Official documentation | Not yet recorded or verified |
| Confirmed facts | None recorded |
| Assumptions and open questions | Identify the relevant product or endpoint; verify access conditions, coverage, and whether multiple employer boards can be evaluated consistently |
| Integration method | Unknown |
| Authentication | Unknown |
| Terms and access restrictions | Unknown; must be reviewed from authoritative sources |
| Attribution requirements | Unknown |
| Rate limits or request constraints | Unknown |
| Storage, retention, and redistribution | Unknown; assess raw payloads, descriptions, local retention, and public-demo use separately |

### Field coverage

| Field or capability | Result | Evidence or notes |
|---|---|---|
| Stable job identifier | UNKNOWN | Not evaluated |
| Original posting URL | UNKNOWN | Not evaluated |
| Application URL | UNKNOWN | Not evaluated |
| Full description | UNKNOWN | Not evaluated |
| Publication or update date | UNKNOWN | Not evaluated |
| Location detail | UNKNOWN | Not evaluated |
| Remote-country eligibility detail | UNKNOWN | Not evaluated |
| Experience wording | UNKNOWN | Not evaluated |

### Representative sample findings

- **Sample date and size:** Not sampled
- **Search inputs or employer boards:** Not selected
- **Relevant-job yield:** Unknown
- **Description coverage:** Unknown
- **Duplicate behaviour:** Unknown
- **Failure modes:** Unknown

### Assessment

- **Advantages:** Not established
- **Risks and disadvantages:** Not established
- **Candidate recommendation:** Pending evidence

## Candidate: Broad job-discovery source

### Decision status and summary

**Status:** Candidate not identified

**Summary:** Leave this candidate unnamed until a credible source with authoritative documentation can be evaluated. Naming a source is not itself evidence that its access method or data use is suitable.

### Candidate overview

| Topic | Findings |
|---|---|
| Candidate name | Not selected |
| Official documentation | Not available until a candidate is identified |
| Confirmed facts | None recorded |
| Assumptions and open questions | Determine whether a credible broad source can provide relevant Canadian jobs, stable identity, original URLs, and sufficient descriptions under documented access conditions |
| Integration method | Unknown |
| Authentication | Unknown |
| Terms and access restrictions | Unknown |
| Attribution requirements | Unknown |
| Rate limits or request constraints | Unknown |
| Storage, retention, and redistribution | Unknown |

### Field coverage

| Field or capability | Result | Evidence or notes |
|---|---|---|
| Stable job identifier | UNKNOWN | Candidate not identified |
| Original posting URL | UNKNOWN | Candidate not identified |
| Application URL | UNKNOWN | Candidate not identified |
| Full description | UNKNOWN | Candidate not identified |
| Publication or update date | UNKNOWN | Candidate not identified |
| Location detail | UNKNOWN | Candidate not identified |
| Remote-country eligibility detail | UNKNOWN | Candidate not identified |
| Experience wording | UNKNOWN | Candidate not identified |

### Representative sample findings

- **Sample date and size:** Not sampled
- **Search inputs:** Not selected
- **Relevant-job yield:** Unknown
- **Description coverage:** Unknown
- **Duplicate behaviour:** Unknown
- **Failure modes:** Unknown

### Assessment

- **Advantages:** Not established
- **Risks and disadvantages:** Not established
- **Candidate recommendation:** Identify a credible candidate before evaluation

## Final source decision

**Decision:** Not made

Complete this section only after comparing the candidates against the rubric.

- **Selected source and v0 path:** Pending
- **Decision rationale:** Pending
- **Evidence reviewed:** Pending
- **Conditions or unresolved risks:** Pending
- **Rejected alternatives and reasons:** Pending
- **Decision date:** Pending
- **Review owner:** Pending

## Required v0 specification changes

After the final decision, update `docs/v0-spec.md` only where supported by the evidence. Record required changes here before editing the specification:

- Name the selected source and choose Path A or Path B.
- Document the stable source identifier and any deterministic fallback.
- Confirm whether `EmployerSource` is required.
- Record source-specific completeness, attribution, request, retention, and display constraints.
- Define configuration needed by the chosen adapter without adding credentials.
- Adjust importer failure handling only if the selected integration requires it.

**Changes currently required:** None established; source evaluation has not begun.
