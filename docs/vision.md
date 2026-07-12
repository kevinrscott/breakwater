# Vision & Product Principles

This is the "why" behind Breakwater — the problem, the priorities, and the principles every feature and technical decision should be checked against. It doesn't change often.

For the exact thing being built right now, see [`v0-spec.md`](v0-spec.md). For what comes after, see [`roadmap.md`](roadmap.md).

## The problem

- Is this job actually junior or early-career?
- Is the listed experience truly required, merely preferred, or ambiguous?
- Does "remote" actually include applicants in Canada?
- Is a hybrid job realistically close enough to commute to?
- Is this the same posting already seen elsewhere?
- Is this a realistic opportunity, a stretch, or clearly unsuitable?
- What's new since the last search?

## Who this is for

The initial user is an early-career technology candidate in Nanaimo, British Columbia, targeting remote roles open to Canadians and nearby hybrid roles. The tool is built for this one real search first, and generalized later only if it proves useful.

## Priority order

Every feature and technical decision follows this order:

1. Find relevant jobs the owner might otherwise miss
2. Avoid hiding realistic opportunities with overly strict filters
3. Reduce time spent reviewing senior, duplicate, irrelevant, or ineligible jobs
4. Make the application reliable enough for daily use
5. Demonstrate strong engineering practice
6. Support additional users only after the personal workflow works

A feature that isn't needed to search for a job this week doesn't belong in v0.

## Product principles

### Utility before platform
The first release is a personal tool. It does not need registration, multiple users, subscriptions, public accounts, complex permissions, resume uploads, notifications, or machine learning.

### Preserve uncertain opportunities
Missing a realistic job is often worse than showing one uncertain result. Breakwater uses explicit match states — `MATCH`, `POSSIBLE`, `STRETCH`, `NOT_A_MATCH`, `UNCLEAR` — and unclear jobs stay visible for review rather than being silently filtered out.

### Explain important decisions
Whenever Breakwater classifies a job as early-career, senior, remote eligible, remote ineligible, hybrid-nearby, stretch, or unclear, it stores and displays the evidence behind that call.

### Rules before AI
The classifier starts with regex, keyword rules, curated title mappings, responsibility signals, and explicit location rules. An LLM may later assist with ambiguous jobs, but it must never become an unexplained source of truth.

### Original postings remain primary
Breakwater is a discovery and review tool, not an application system. It preserves the original application URL, prefers direct-employer links, avoids re-hosting restricted content, and never auto-applies or pretends to replace an employer's application process.

### Measure quality
Classification quality is eventually measured against a labelled fixture dataset. Portfolio claims use actual measured results rather than vague statements like "AI-powered job matching."

## Target search profile

### Location

**Include:** remote jobs explicitly or likely open to Canadian applicants (with unclear eligibility routed to a separate queue), hybrid jobs within a configurable distance of Nanaimo, and nearby on-site roles only when explicitly enabled.

**Exclude or separate:** US-only remote roles, jobs restricted to unsupported countries/provinces, hybrid jobs requiring regular Vancouver commuting, and jobs with conflicting or unreadable location information.

### Career tracks

Three tracks, kept visibly separate — an interim role should never be presented as equivalent to software development:

**Primary development roles** — e.g. Junior Software Developer/Engineer, Backend/Full-Stack/Web Developer, Python Developer, New Graduate Software Engineer, WordPress Developer, Integration Developer.

**Adjacent technology roles** — e.g. QA Analyst/Automation Engineer, Application Support Analyst, Technical Support Specialist, Implementation Specialist, Junior Systems Analyst, IT Support Technician.

**Interim roles** — e.g. Data Entry, Administrative Assistant, Customer Support, Data Annotator, Content Moderator, Junior Technical Writer.

> **Open question:** the rules for actually classifying a job into one of these three tracks (and into `workplace_type`) aren't written yet — see the flagged gap in [`v0-spec.md`](v0-spec.md#data-model).

## Major risks

| Risk | Mitigation |
|---|---|
| Weak source coverage | Validate sample data before building the full importer |
| Partial descriptions (snippet-only APIs) | Store content completeness; classify uncertain jobs as `UNCLEAR` |
| False negatives (strict filters hide real opportunities) | Keep `POSSIBLE`/`STRETCH`/`UNCLEAR` queues visible |
| False positives (too much noise) | Save corrections, build regression tests, tune from real use |
| Source redistribution restrictions | Use official endpoints, document terms, preserve attribution, use synthetic demo data publicly |
| v0 becomes disposable | Keep adapters, classification modules, stable identifiers, Postgres, and tests from day one |
| Overengineering | v0 uses only Django, PostgreSQL, Docker Compose, one source, simple rules |
| Scope creep | Resume matching, AI, and alerts stay optional until after the deployed portfolio version |
| Unsafe handling of third-party content | Render as plain text by default; sanitize server-side if formatting is ever preserved |

## Final principle

Breakwater doesn't need to contain every job. It needs to make a focused set of opportunities more actionable.

It succeeds when it finds jobs the owner might otherwise miss, makes daily review faster, removes obvious senior and ineligible roles, preserves realistic and uncertain opportunities, explains every important classification, improves from real corrections, measures its own quality, and demonstrates disciplined full-stack engineering.
