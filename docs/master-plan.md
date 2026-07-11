\# Breakwater — Final Product and Implementation Plan (v1.3)



\*\*Document status:\*\* Final master plan, revision 1.3  

\*\*Primary goal:\*\* Help the owner find relevant jobs faster and miss fewer realistic opportunities  

\*\*Secondary goal:\*\* Evolve the same working codebase into a strong portfolio, GitHub, and resume project — built with a security-conscious, production-minded engineering baseline, not just a working one  

\*\*Initial user:\*\* An early-career technology candidate in Nanaimo, British Columbia, targeting remote roles open to Canadians and nearby hybrid roles  

\*\*Delivery strategy:\*\* Ship a useful personal version first, validate it through real job searching, then build the portfolio version around proven needs



\*\*Changes in this revision:\*\*



\- Renamed the product and updated repository, package, documentation, README, and résumé examples to use Breakwater consistently



\- Refined security language to avoid claiming that a checklist guarantees security

\- Clarified what CI secret scanning can and cannot prevent, and added local pre-commit and credential-rotation guidance

\- Clarified failure behavior for single-source imports versus multi-board ATS imports

\- Split plain-text descriptions from preserved raw HTML

\- Made stable source identifiers explicitly non-null and deterministic

\- Replaced Nanaimo-specific distance field naming with a configurable search origin

\- Added dependency locking and pinned runtime/container versions

\- Expanded the production deployment checklist for HTTPS, cookies, CSRF, HSTS, proxy headers, and log hygiene

\- Retained rough time-box ranges and the v0-first delivery strategy



---



\# 1. Executive Summary



Breakwater is a personal job-discovery and review tool for early-career candidates.



Most job boards are weak at answering the questions that matter most:



\- Is this job actually junior or early-career?

\- Is the listed experience truly required, merely preferred, or ambiguous?

\- Does “remote” actually include applicants in Canada?

\- Is a hybrid job realistically close enough to commute to?

\- Is this the same posting already seen elsewhere?

\- Is this a realistic opportunity, a stretch, or clearly unsuitable?

\- What is new since the last search?



Breakwater will collect jobs from permitted APIs and public employer job-board endpoints, normalize them, classify them using deterministic and explainable rules, and show a focused daily review queue.



The project will be built in two stages:



\## v0 — Personal Utility



A small Django application that can be completed quickly and used for a real job search.



It will:



\- Import jobs from one validated source

\- Avoid duplicate rows during reimports

\- Extract experience requirements

\- Detect obvious senior roles

\- Classify remote-Canada eligibility

\- Handle nearby hybrid locations simply

\- Show new jobs

\- Allow save, hide, and applied actions

\- Link to the original posting

\- Explain its classifications



\## v1 — Portfolio Product



The same codebase will later gain:



\- Multiple source adapters

\- A Next.js frontend

\- PostGIS

\- Better classification and evaluation

\- Similarity-based deduplication

\- Scheduled imports

\- CI and fuller testing

\- Public deployment with synthetic or approved data

\- Architecture documentation and a portfolio case study



The key principle is:



> Breakwater must become useful for the owner’s real job search before it becomes a polished portfolio product.



---



\# 2. Priority Order



Every feature and technical decision must follow this order:



1\. Find relevant jobs the owner might otherwise miss

2\. Avoid hiding realistic opportunities with overly strict filters

3\. Reduce time spent reviewing senior, duplicate, irrelevant, or ineligible jobs

4\. Make the application reliable enough for daily use

5\. Demonstrate strong engineering practice

6\. Support additional users only after the personal workflow works



A feature that is not needed to search for a job this week does not belong in v0.



---



\# 3. Product Principles



\## 3.1 Utility before platform



The first release is a personal tool.



It does not need:



\- Registration

\- Multiple users

\- Subscriptions

\- Public accounts

\- Complex permissions

\- Resume uploads

\- Notifications

\- Machine learning



\## 3.2 Preserve uncertain opportunities



Missing a realistic job is often worse than showing one uncertain result.



Breakwater must use explicit match states:



```text

MATCH

POSSIBLE

STRETCH

NOT\_A\_MATCH

UNCLEAR

```



Unclear jobs should remain visible for review.



\## 3.3 Explain important decisions



Whenever Breakwater classifies a job as:



\- Early-career

\- Senior

\- Remote eligible

\- Remote ineligible

\- Hybrid nearby

\- Stretch

\- Unclear



it should store and display the evidence.



\## 3.4 Rules before AI



The initial classifier will use:



\- Regex

\- Keyword rules

\- Curated title mappings

\- Responsibility signals

\- Explicit location rules



An LLM may later assist with ambiguous jobs, but it must never become an unexplained source of truth.



\## 3.5 Original postings remain primary



Breakwater is a discovery and review tool.



It should:



\- Preserve the original application URL

\- Prefer direct-employer links

\- Avoid re-hosting restricted content

\- Avoid automatically applying

\- Avoid pretending to replace employer application systems



\## 3.6 Measure quality



Classification quality must eventually be measured against a labelled fixture dataset.



Portfolio claims should use actual results rather than vague statements such as “AI-powered job matching.”



---



\# 4. Target Search Profile



The application should eventually be configurable, but v0 can optimize for the owner’s real search.



\## 4.1 Location preferences



Include:



\- Remote jobs explicitly open to Canadian applicants

\- Remote jobs likely open to Canadian applicants

\- Remote jobs with unclear geographic eligibility in a separate queue

\- Hybrid jobs within a configurable distance of Nanaimo

\- Nearby on-site roles only when explicitly enabled



Exclude or separate:



\- United States-only remote roles

\- Jobs restricted to unsupported countries or provinces

\- Hybrid jobs requiring regular Vancouver commuting

\- Jobs with conflicting location information

\- Jobs whose location cannot be understood reliably



\## 4.2 Career tracks



\### Primary development roles



Examples:



\- Junior Software Developer

\- Junior Software Engineer

\- Backend Developer

\- Full-Stack Developer

\- Web Developer

\- Application Developer

\- Python Developer

\- Junior Programmer

\- New Graduate Software Engineer

\- Associate Software Developer

\- WordPress Developer

\- Integration Developer



\### Adjacent technology roles



Examples:



\- QA Analyst

\- Software Tester

\- Junior QA Automation Engineer

\- Application Support Analyst

\- Technical Support Specialist

\- Implementation Specialist

\- Junior Systems Analyst

\- IT Support Technician

\- Website Administrator

\- Product Support Specialist

\- Data Operations Specialist

\- Technical Customer Support



\### Interim roles



Examples:



\- Data Entry

\- Administrative Assistant

\- Customer Support

\- Office Assistant

\- Operations Assistant

\- Data Annotator

\- Content Moderator

\- Junior Technical Writer

\- Entry-Level Operations Coordinator



These tracks must remain visibly separate.



An interim role should never be presented as equivalent to software development.



---



\# 5. Delivery Strategy



\## 5.1 v0 — Personal Utility



\*\*Goal:\*\* Get real leads into daily use quickly.



\*\*Expected scope:\*\* Small enough to complete without building the full platform.



\*\*Frontend:\*\* Django Admin with custom list views and filters, or one simple Django template if Admin becomes limiting.



\*\*Backend:\*\* Django and PostgreSQL.



\*\*Sources:\*\* One validated source.



\*\*Classification:\*\* Simple but structured rule modules.



\*\*Location:\*\* Manual city coordinates or simple cached geocoding plus Haversine distance.



\*\*Deployment:\*\* Local only.



\## 5.2 v1 — Portfolio Product



\*\*Goal:\*\* Evolve the validated tool into a public, measurable, documented full-stack project.



\*\*Frontend:\*\* Next.js.



\*\*Backend:\*\* Existing Django API.



\*\*Database:\*\* Existing PostgreSQL upgraded with PostGIS.



\*\*Sources:\*\* Broad API plus selected employer ATS adapters.



\*\*Classification:\*\* Versioned, evaluated, evidence-based.



\*\*Deployment:\*\* Public demo using synthetic or permitted data.



---



\# 6. v0 Definition of Done



v0 is complete when:



\- \[ ] One command imports jobs from one validated source

\- \[ ] Re-running the import does not create duplicate rows

\- \[ ] Jobs show required and preferred experience when extractable

\- \[ ] Obvious senior jobs are classified appropriately

\- \[ ] Remote-Canada eligibility is classified as yes, no, or unclear

\- \[ ] Hybrid distance works for supported locations

\- \[ ] Jobs show a match band and readable explanation

\- \[ ] Classification evidence is preserved

\- \[ ] New jobs can be distinguished from previously reviewed jobs

\- \[ ] Jobs can be saved, hidden, and marked applied

\- \[ ] The original posting can be opened

\- \[ ] Core classification and import behaviour has automated tests

\- \[ ] A small CI workflow runs those tests, plus secret and dependency scanning

\- \[ ] Source content is rendered as plain text (or sanitized), never as raw HTML

\- \[ ] The tool has been used for at least one real week of job searching



The week of usage is not a development freeze.



During that week:



\- Fix bugs

\- Tune rules

\- Record false positives

\- Record false negatives

\- Note repetitive workflow problems

\- Track which source produced useful opportunities



The purpose is to collect evidence before finalizing v1 priorities.



---



\# 7. v0 Non-Goals



v0 will not include:



\- Next.js

\- PostGIS

\- Multiple job sources

\- Similarity-based deduplication

\- Redis

\- Celery

\- Resume uploads

\- Semantic search

\- Authentication

\- Multiple users

\- Public deployment

\- Email alerts

\- Full application-history tracking

\- Complex company normalization

\- Machine-learning classification



---



\# 8. Technology Stack



\## 8.1 v0 stack



\- Python

\- Django

\- PostgreSQL

\- Docker

\- Docker Compose

\- A committed Python dependency lockfile

\- A pinned Python version

\- A pinned PostgreSQL container version

\- Django Admin

\- pytest

\- pytest-django

\- Ruff

\- GitHub Actions

\- gitleaks (secret scanning)

\- pip-audit (dependency vulnerability scanning)

\- One import management command



PostgreSQL should be used from the beginning.



Use reproducible dependency and runtime versions:



\- Commit a Python dependency lockfile, such as `uv.lock` when using `uv`

\- Pin the supported Python version

\- Pin the PostgreSQL image version

\- Avoid floating Docker tags such as `latest`





SQLite should not be used because it would create unnecessary differences in:



\- JSON behaviour

\- Constraints

\- Text search

\- Migrations

\- Database-specific queries

\- Later PostGIS adoption



\## 8.2 v1 additions



Add only when needed:



\- Django REST Framework

\- django-filter

\- Next.js

\- TypeScript

\- Tailwind CSS

\- Zod

\- Playwright

\- PostGIS

\- TanStack Query

\- React Hook Form

\- Pyright or mypy

\- Redis

\- Celery

\- Celery Beat

\- pgvector

\- S3-compatible storage

\- Error monitoring



\## 8.3 Security Baseline



These apply starting in v0, not just at deployment time. They are cheap now and expensive to retrofit.



\*\*Third-party content is untrusted:\*\*



\- Job descriptions come from external sources and may contain raw HTML or scripts

\- Render descriptions as plain text by default

\- If formatting is preserved later, sanitize server-side (e.g. `bleach`) before storage or display

\- Never render raw source content with Django's `|safe` filter or React's `dangerouslySetInnerHTML` without sanitization first



\*\*Django configuration hygiene (from v0, enforced before any non-local deployment):\*\*



\- `SECRET\_KEY` read from an environment variable, never committed

\- `.env` excluded from Git

\- `.env.example` contains placeholders only

\- `DEBUG = False` outside local development

\- `ALLOWED\_HOSTS` set explicitly, no wildcard

\- Secure cookie and CSRF settings enabled once served over HTTPS



\*\*CI enforcement, not just written rules:\*\*



\- Secret scanning on every push (e.g. `gitleaks`) to detect accidentally committed credentials as early as possible

\- An optional local pre-commit secret scan may be added to catch credentials before they are committed

\- If a credential is ever exposed, rotate or revoke it immediately rather than relying on history cleanup alone

\- Dependency vulnerability scanning (e.g. `pip-audit`, and `npm audit` once the frontend exists)

\- Both run alongside Ruff and pytest in the same workflow (§21)



\*\*Outbound requests to job sources:\*\*



\- Explicit timeouts on every HTTP call — never an unbounded request

\- Retry with backoff on transient failures, capped attempts

\- Every outbound request must fail clearly rather than hang indefinitely

\- When one adapter processes multiple employer boards, one failing board must not prevent the remaining boards from being processed



---



\# 9. v0 Architecture



```text

┌──────────────────────────────────────┐

│ Django Admin / Simple Django View   │

│                                      │

│ New jobs                             │

│ Search and filtering                 │

│ Classification evidence              │

│ Save / hide / applied actions        │

│ Original application links           │

└──────────────────┬───────────────────┘

&nbsp;                  │

┌──────────────────▼───────────────────┐

│ Django Application                   │

│                                      │

│ Import command                       │

│ Source adapter                       │

│ Normalization                        │

│ Experience classification            │

│ Seniority classification             │

│ Remote eligibility                   │

│ Location matching                    │

└──────────────────┬───────────────────┘

&nbsp;                  │

┌──────────────────▼───────────────────┐

│ PostgreSQL                           │

│                                      │

│ Jobs                                 │

│ Optional employer sources            │

│ Review state                         │

│ Raw source payloads                  │

└──────────────────────────────────────┘

```



v0 remains a modular monolith.



Simple does not mean placing all logic in one management command.



---



\# 10. Suggested v0 Repository Structure



```text

breakwater/

├── app/

│   ├── config/

│   ├── breakwater/

│   │   ├── jobs/

│   │   │   ├── admin.py

│   │   │   ├── models.py

│   │   │   ├── services.py

│   │   │   └── management/

│   │   │       └── commands/

│   │   │           └── import\_jobs.py

│   │   │

│   │   ├── ingestion/

│   │   │   ├── adapters/

│   │   │   ├── normalization.py

│   │   │   └── types.py

│   │   │

│   │   ├── classification/

│   │   │   ├── experience.py

│   │   │   ├── seniority.py

│   │   │   ├── remote.py

│   │   │   ├── matching.py

│   │   │   └── types.py

│   │   │

│   │   └── locations/

│   │       ├── cities.py

│   │       └── distance.py

│   │

│   ├── tests/

│   │   ├── fixtures/

│   │   ├── test\_imports.py

│   │   ├── test\_experience.py

│   │   ├── test\_seniority.py

│   │   └── test\_remote.py

│   │

│   ├── manage.py

│   └── pyproject.toml

│

├── docs/

│   ├── product-vision.md

│   ├── implementation-roadmap.md

│   ├── v0-specification.md

│   ├── source-notes.md

│   └── usage-log.md

│

├── .github/

│   └── workflows/

│       └── backend.yml

│

├── compose.yaml

├── Dockerfile

├── .env.example

├── .gitignore

├── AGENTS.md

├── README.md

└── LICENSE

```



The repository may later become a monorepo when Next.js is added.



Do not create an `apps/web` directory until the frontend actually exists.



---



\# 11. Source Selection



Source quality is the most important early unknown.



Before building the importer, perform a short source check.



\## 11.1 Half-day source check



Test one broad source and one direct-employer ATS option.



For each candidate, inspect approximately 30–50 postings where possible.



Evaluate:



\- Number of relevant Canadian jobs

\- Full description versus snippet availability

\- Stable job identifiers

\- Original application URLs

\- Publication dates

\- Location quality

\- Remote-country information

\- Experience wording

\- Duplicate frequency

\- Rate limits

\- Terms and attribution requirements



\## 11.2 Source Path A — Broad discovery source



Choose this path if the broad API produces enough relevant Canadian jobs.



v0 then includes:



\- One broad source adapter

\- Configured search queries

\- No employer registry initially

\- Search result import

\- Partial-description detection

\- Rate-limit handling



\## 11.3 Source Path B — Employer ATS source



Choose this path if direct employer boards produce much better data.



v0 then includes:



\- One ATS adapter

\- Five to ten target employers

\- A small `EmployerSource` table

\- Board identifiers

\- Per-employer import handling



Do not begin with 15–30 employers.



Start with a small set of high-value employers and expand only after imports work.



\## 11.4 Source compliance



For the chosen source, record:



\- Integration method

\- Terms or API documentation

\- Attribution requirements

\- Rate limits

\- Supported fields

\- Description completeness

\- Data-retention concerns

\- Review date

\- Known restrictions



Breakwater must not:



\- Scrape LinkedIn

\- Scrape Indeed

\- Bypass CAPTCHAs

\- Bypass access controls

\- Ignore rate limits

\- Invent permissions

\- Commit source credentials

\- Publicly redistribute restricted content



---



\# 12. v0 Data Model



A single main `Job` table is acceptable for v0, provided it contains the fields needed to avoid immediate migration pain.



\## 12.1 Job



```text

Job



id



source\_type

source\_job\_id

source\_url

application\_url



title

company\_name

location\_text

description\_text

description\_html\_raw

content\_completeness



posted\_at

first\_seen\_at

last\_seen\_at

last\_changed\_at

is\_active



years\_required\_min

years\_required\_max

years\_preferred

experience\_requirement\_type



remote\_canada\_eligibility

remote\_countries

workplace\_type



office\_latitude

office\_longitude

distance\_km\_from\_origin



career\_track

role\_family

match\_band



classifier\_version

classification\_explanation

classification\_evidence



raw\_payload

raw\_payload\_hash



first\_viewed\_at

saved\_at

hidden\_at

applied\_at

notes



created\_at

updated\_at

```



\## 12.2 Required constraints



```text

source\_job\_id NOT NULL

source\_job\_id NOT BLANK

UNIQUE(source\_type, source\_job\_id)

```



This is the primary protection against duplicate rows during reimports.



If the source does not provide a stable identifier, derive one deterministically from documented stable fields. Do not generate a new random identifier on each import.



\## 12.3 Content completeness



```text

FULL

PARTIAL

SNIPPET

UNKNOWN

```



A partial description must reduce classification confidence.



`description\_text` is the only description field used for classification and default rendering. `description\_html\_raw` is preserved only for audit or later reprocessing and must never be rendered directly.



\## 12.4 Review state



Do not use one mutually exclusive status field for all user actions.



A job can be:



\- Viewed and saved

\- Saved and applied

\- Applied and later expired

\- Viewed and later hidden



Use timestamps:



```text

first\_viewed\_at

saved\_at

hidden\_at

applied\_at

```



A job is new when:



```text

first\_viewed\_at IS NULL

```



\## 12.5 Optional EmployerSource model



Only add this in v0 if Source Path B is selected.



```text

EmployerSource



id

company\_name

source\_type

board\_identifier

careers\_url

is\_active

last\_import\_at

last\_success\_at

consecutive\_failures

notes

created\_at

updated\_at

```



---



\# 13. Ingestion Design



The management command should orchestrate the import, not contain all business logic.



`source\_job\_id` must be non-null and non-blank. If a source does not provide a stable identifier, derive a documented deterministic identifier from stable source fields such as the canonical application URL or a normalized combination of source, company, title, location, and publication identifier. Never generate a random ID per import.



\## 13.1 Flow



```text

Fetch raw jobs

&nbsp;     ↓

Validate source fields

&nbsp;     ↓

Normalize source record

&nbsp;     ↓

Calculate payload hash

&nbsp;     ↓

Classify experience

&nbsp;     ↓

Classify seniority

&nbsp;     ↓

Classify remote eligibility

&nbsp;     ↓

Resolve known location

&nbsp;     ↓

Calculate distance if possible

&nbsp;     ↓

Determine career track

&nbsp;     ↓

Determine match band

&nbsp;     ↓

Upsert using source\_type + source\_job\_id

&nbsp;     ↓

Set first\_seen / last\_seen / last\_changed

```



\## 13.2 Adapter contract



```python

class JobSourceAdapter(Protocol):

&nbsp;   source\_name: str



&nbsp;   def fetch\_jobs(self) -> Iterable\[RawJob]:

&nbsp;       ...



&nbsp;   def normalize\_job(self, raw\_job: RawJob) -> NormalizedJobInput:

&nbsp;       ...

```



There may only be one adapter in v0, but using a small contract prevents the management command from becoming source-specific.



`fetch\_jobs` must apply an explicit request timeout and a capped retry-with-backoff policy (see §8.3). A failed single-source v0 import should terminate with a clear reportable error rather than hang. When an ATS adapter processes multiple employer boards, failures should be isolated per board so the remaining boards can continue.



\## 13.3 Idempotent reimports



On import:



\- Create a job when the source ID is new

\- Update `last\_seen\_at` when it already exists

\- Update the record when the payload hash changes

\- Set `last\_changed\_at` only when meaningful content changes

\- Preserve review timestamps

\- Do not overwrite user notes

\- Do not reset saved, hidden, viewed, or applied state



---



\# 14. Experience Classification



\## 14.1 Experience fields



Store experience separately:



```text

years\_required\_min

years\_required\_max

years\_preferred

experience\_requirement\_type

```



Requirement types:



```text

REQUIRED

PREFERRED

NICE\_TO\_HAVE

FLEXIBLE

AMBIGUOUS

NOT\_FOUND

```



\## 14.2 Examples



Correct handling:



```text

“1+ years required”

required\_min = 1

```



```text

“1–2 years of professional experience”

required\_min = 1

required\_max = 2

```



```text

“2 years preferred”

preferred = 2

requirement\_type = PREFERRED

```



```text

“Experience with Python”

no numeric requirement

```



```text

“5 years of combined education and experience”

must not automatically become 5 professional years

```



\## 14.3 Match bands



\### MATCH



Typical signals:



\- Junior

\- Entry level

\- New graduate

\- Associate

\- Internship

\- Zero to one year required

\- No leadership signals



\### POSSIBLE



Typical signals:



\- Zero to two years required

\- Up to three years preferred

\- Flexible equivalent-experience wording

\- Appropriate responsibilities

\- No clear senior ownership



This should be the default useful queue.



\### STRETCH



Typical signals:



\- Two to three years required

\- Strong role fit

\- No staff, lead, architect, manager, or director expectations

\- No team-management responsibility

\- Explanation states why it is a stretch



\### NOT\_A\_MATCH



Typical signals:



\- Senior, staff, principal, lead, architect, manager, or director title

\- Four or more years explicitly required

\- Team-management responsibility

\- Hiring responsibility

\- Organization-wide technical ownership

\- Strategic engineering ownership



\### UNCLEAR



Use when:



\- Only a snippet is available

\- Required and preferred wording conflicts

\- Experience cannot be extracted

\- Title and responsibilities disagree

\- Content is incomplete



Unclear jobs remain reviewable.



---



\# 15. Seniority Classification



Strong negative signals include:



```text

senior

staff

principal

lead engineer

architect

manager

director

head of

manage a team

performance management

hire engineers

set organization-wide strategy

own engineering standards

```



Rules must be contextual.



Examples:



```text

“Lead a small feature”

```



does not automatically mean a Lead-level role.



```text

“Lead Engineer”

```



is a strong seniority signal.



```text

“Mentor junior developers”

```



may indicate a more senior role, but should be combined with other evidence.



The classifier should record:



\- Matched phrase

\- Rule identifier

\- Positive or negative signal

\- Impact on the match band



---



\# 16. Remote Eligibility



The field should be:



```text

remote\_canada\_eligibility

```



Values:



```text

YES

NO

UNCLEAR

```



\## 16.1 YES



Use when the posting explicitly indicates:



\- Canada remote

\- Open to Canadian applicants

\- Remote across Canada

\- Eligible Canadian provinces including British Columbia

\- A Canadian location with a clearly remote workplace arrangement



\## 16.2 NO



Use when the posting explicitly indicates:



\- United States only

\- Must reside in a specific unsupported country

\- Must reside in an unsupported state or province

\- Remote but legally restricted outside Canada



\## 16.3 UNCLEAR



Use when:



\- The posting only says “remote”

\- Geographic eligibility is omitted

\- Location fields conflict

\- Only a snippet is available

\- A timezone is listed without residency rules



The word “remote” alone must never produce `YES`.



---



\# 17. Hybrid Distance



Haversine distance is simple after coordinates exist.



The hard part is resolving location text into coordinates.



\## 17.1 v0 strategy



Use a small curated city coordinate dictionary.



Initial locations may include:



```text

Nanaimo

Parksville

Qualicum Beach

Duncan

Courtenay

Comox

Victoria

Vancouver

Burnaby

Richmond

Surrey

New Westminster

```



Each city entry should contain:



```text

city

province

latitude

longitude

```



Configure the search origin rather than hardcoding it into field names:



```text

SEARCH\_ORIGIN\_NAME=Nanaimo, BC

SEARCH\_ORIGIN\_LATITUDE=...

SEARCH\_ORIGIN\_LONGITUDE=...

DEFAULT\_HYBRID\_RADIUS\_KM=...

```



\## 17.2 Location handling



If a posting contains a known city:



\- Resolve it to coordinates

\- Calculate distance from Nanaimo

\- Store the distance



If it contains an ambiguous region:



\- Keep the raw location text

\- Leave distance null

\- Mark the location result unclear



Do not guess coordinates for:



```text

Greater Vancouver

British Columbia

Vancouver Island

Multiple locations

Nanaimo or Vancouver

```



unless a rule can safely resolve them.



\## 17.3 v1 upgrade



PostGIS and cached geocoding can later replace the curated city dictionary.



---



\# 18. Classification Evidence



Evidence should exist in v0.



A JSON field is sufficient.



Example:



```json

{

&nbsp; "experience": \[

&nbsp;   {

&nbsp;     "rule\_id": "EXP\_REQUIRED\_RANGE",

&nbsp;     "text": "1-2 years of software development experience",

&nbsp;     "type": "required\_range",

&nbsp;     "minimum": 1,

&nbsp;     "maximum": 2

&nbsp;   }

&nbsp; ],

&nbsp; "seniority": \[],

&nbsp; "remote": \[

&nbsp;   {

&nbsp;     "rule\_id": "REMOTE\_CANADA\_EXPLICIT",

&nbsp;     "text": "This role is open to applicants across Canada",

&nbsp;     "result": "YES"

&nbsp;   }

&nbsp; ]

}

```



Also store a readable explanation:



```text

Possible match because the posting requests 1–2 years of experience,

explicitly accepts applicants across Canada, and contains no seniority

or people-management signals.

```



This allows:



\- Immediate trust

\- Easier debugging

\- User correction

\- Regression fixtures later

\- Portfolio demonstrations later



---



\# 19. v0 Interface



Django Admin should be customized to act as a usable review dashboard.



\## 19.1 List columns



Show:



\- New indicator

\- Match band

\- Title

\- Company

\- Career track

\- Workplace type

\- Remote-Canada eligibility

\- Required years

\- Preferred years

\- Distance

\- Posted date

\- First seen

\- Saved

\- Applied

\- Source



\## 19.2 Filters



Add filters for:



\- New

\- Match band

\- Career track

\- Workplace type

\- Remote eligibility

\- Saved

\- Hidden

\- Applied

\- Source

\- First-seen date

\- Posted date



\## 19.3 Actions



Support:



\- Mark viewed

\- Save

\- Unsave

\- Hide

\- Unhide

\- Mark applied

\- Clear applied

\- Open original posting



Django Admin may require a small custom link column for the original posting.



\## 19.4 Default review view



The default useful queue should be approximately:



```text

hidden\_at IS NULL

AND applied\_at IS NULL

AND match\_band IN (MATCH, POSSIBLE, STRETCH, UNCLEAR)

ORDER BY first\_seen\_at DESC

```



\## 19.5 Rendering source content safely



Job descriptions are third-party, untrusted content. Classify and display `description\_text` by default. Preserve `description\_html\_raw` only when the source provides it and it is useful for later reprocessing. Never render `description\_html\_raw` directly, never mark source content `|safe`, and never bypass Django's default auto-escaping. If formatted descriptions are added later, sanitize into a separate derived field before display. See §8.3.



---



\# 20. Minimum v0 Testing



Do not postpone all testing until v1.



At minimum, test:



\## 20.1 Experience



\- Extracts `1+ years`

\- Extracts `1–2 years`

\- Extracts `2 to 3 years`

\- Separates preferred from required

\- Does not treat “experience with Python” as a number

\- Handles missing experience

\- Handles conflicting phrases



\## 20.2 Seniority



\- Detects Senior titles

\- Detects Staff and Principal titles

\- Detects management roles

\- Does not classify “lead a feature” as automatically Lead-level

\- Detects team-management responsibility



\## 20.3 Remote eligibility



\- Accepts explicit Canada-remote language

\- Rejects explicit US-only language

\- Keeps unspecified remote eligibility unclear

\- Handles conflicting location text



\## 20.4 Import behaviour



\- Same source job ID does not duplicate

\- Changed payload updates the job

\- Unchanged payload preserves `last\_changed\_at`

\- Reimport preserves saved and applied state

\- Source failure produces a readable error



A small suite of approximately 15–25 tests is enough for v0.



---



\# 21. v0 Continuous Integration



Add a small GitHub Actions workflow early.



Run:



```text

Install Python dependencies

Ruff lint

Ruff format check

pytest

Django migration check

Secret scan (gitleaks)

Dependency vulnerability scan (pip-audit)

```



This keeps engineering practices real instead of adding them only during portfolio polish. The secret and dependency scans matter early. CI scanning can detect an accidental commit quickly, but it does not prevent the secret from entering Git history. Use environment variables, keep `.env` out of Git, optionally add a local pre-commit scan, and rotate any exposed credential immediately.



---



\# 22. v0 Implementation Order



\## Step 1 — Define the exact v0



Create:



```text

docs/v0-specification.md

```



Include:



\- One selected source

\- Exact match-band rules

\- Exact fields

\- Explicit non-goals

\- Definition of done



\## Step 2 — Validate the source



Sample approximately 30–50 jobs.



Choose Source Path A or B.



Record findings in:



```text

docs/source-notes.md

```



\## Step 3 — Bootstrap the repository



Add:



\- Django

\- PostgreSQL

\- Docker Compose

\- pytest

\- Ruff

\- GitHub Actions

\- README

\- `.env.example`



\## Step 4 — Add the Job model



Implement:



\- Stable source identity

\- Raw payload storage

\- First-seen and last-seen timestamps

\- Review timestamps

\- Classification fields

\- Unique constraint



\## Step 5 — Add the source adapter and import command



Implement:



\- Fetch

\- Normalize

\- Hash

\- Upsert

\- Error reporting

\- Idempotency tests



\## Step 6 — Add classification modules



Implement separately:



\- Experience extraction

\- Seniority

\- Remote eligibility

\- Career track

\- Match band

\- Explanation

\- Evidence JSON



\## Step 7 — Add location handling



Implement:



\- Curated city coordinates

\- Haversine distance

\- Unknown-location behaviour

\- Distance display



\## Step 8 — Customize Django Admin



Implement:



\- Columns

\- Filters

\- Actions

\- Original-posting links

\- Useful default ordering



\## Step 9 — Use it for a real week



Record:



\- Useful jobs found

\- False positives

\- False negatives

\- Wrong experience extraction

\- Wrong remote classifications

\- Missing filters

\- Repetitive actions

\- Source quality



\## Step 10 — Decide v1 priorities using evidence



Do not follow the v1 roadmap blindly.



Promote features based on real limitations discovered during use.



---



\# 23. Initial GitHub Issues



Create these first:



```text

1\. docs: define the v0 personal utility specification

2\. research: validate the first job source

3\. chore: initialize Django and PostgreSQL workspace

4\. chore: add Docker Compose development environment

5\. ci: add backend linting and tests

6\. feat(jobs): add the v0 job model

7\. feat(ingestion): define the source adapter contract

8\. feat(ingestion): import jobs from the first source

9\. feat(classification): extract required and preferred experience

10\. feat(classification): detect seniority and leadership signals

11\. feat(classification): classify remote Canada eligibility

12\. feat(classification): add match bands and explanations

13\. feat(location): calculate distance for supported cities

14\. feat(admin): add the job review dashboard

15\. test: cover import idempotency and classifier edge cases

16\. docs: record findings from the first week of real use

17\. planning: define evidence-based v1 priorities

```



---



\# 24. v1 Portfolio Roadmap



v1 begins only after v0 is useful.



\## B1 — Improve Classification



\*\*Rough time-box:\*\* 1–2 weeks (evenings/weekends)



Add:



\- Separate classification models if justified

\- Classifier versioning

\- Evidence spans

\- Rule identifiers

\- Confidence

\- User correction workflow

\- Regression fixtures



Completion criteria:



\- Every classification is explainable

\- Corrected mistakes become tests

\- Rules can be rerun safely



\## B2 — Add a Second Source



\*\*Rough time-box:\*\* 1–2 weeks



Add:



\- One ATS adapter

\- Shared adapter contract

\- Employer source registry

\- Source-specific failure handling

\- Multiple source records per normalized job if needed



Completion criteria:



\- One source failure does not stop the other

\- Reimports remain idempotent

\- Direct employer links are preferred



\## B3 — Build the Next.js Frontend



\*\*Rough time-box:\*\* 1–2 weeks



Add:



\- Next.js

\- TypeScript

\- Tailwind

\- Django REST Framework

\- Search dashboard

\- Job cards

\- Job detail view

\- URL-based filters

\- Save, hide, and applied actions

\- Responsive layout



Completion criteria:



\- The Django Admin workflow is fully represented

\- Search URLs are shareable

\- Loading, empty, and error states exist

\- Job descriptions render as text/markdown-safe content, never via `dangerouslySetInnerHTML` on raw source data (§8.3)



\## B4 — Upgrade Location with PostGIS



\*\*Rough time-box:\*\* 3–5 days



Add:



\- PostGIS

\- Structured locations

\- Configurable radius

\- Geocoding cache

\- Geocoding confidence

\- Radius queries



Completion criteria:



\- Remote Canada plus hybrid radius works reliably

\- Ambiguous locations remain explicit

\- Low-confidence geocodes do not silently determine eligibility



\## B5 — Evaluation and Deduplication



\*\*Rough time-box:\*\* 1 week



Add:



\- Labelled fixture dataset

\- Evaluation command

\- Published metrics

\- Similarity-based duplicate candidates

\- Preferred source selection

\- Incorrect-merge correction



Measure:



\- Senior-job leakage

\- Valid early-career recall

\- Required-years accuracy

\- Preferred-years accuracy

\- Remote eligibility accuracy

\- Role-family accuracy

\- Duplicate precision



\## B6 — Additional Sources and Scheduling



\*\*Rough time-box:\*\* 1–2 weeks



Add:



\- Lever or Ashby

\- Source-health reporting

\- Redis

\- Celery

\- Scheduled imports

\- Retry policies

\- Duplicate-task prevention

\- Failed-task visibility



Only add Celery and Redis when manual imports are genuinely inconvenient.



\## B7 — Deployment and Portfolio Polish



\*\*Rough time-box:\*\* 1–2 weeks



Add:



\- Production configuration, specifically:

&nbsp; - `SECRET\_KEY` from a platform secret store, never committed

&nbsp; - `DEBUG = False`

&nbsp; - `ALLOWED\_HOSTS` set explicitly

&nbsp; - HTTPS enforced

&nbsp; - `SECURE\_SSL\_REDIRECT = True`

&nbsp; - `SESSION\_COOKIE\_SECURE = True`

&nbsp; - `CSRF\_COOKIE\_SECURE = True`

&nbsp; - `CSRF\_TRUSTED\_ORIGINS` configured explicitly

&nbsp; - HSTS enabled after HTTPS is verified

&nbsp; - Proxy SSL headers configured correctly for the hosting platform

&nbsp; - Application logs reviewed to ensure they do not expose secrets or complete sensitive API responses

\- Public frontend

\- Hosted API

\- Hosted PostgreSQL

\- Synthetic or approved demo data

\- Architecture diagram

\- Demo video

\- Complete README

\- ADRs

\- Known limitations

\- Error monitoring

\- Portfolio case study



Completion criteria:



\- Public demo works

\- CI passes, including secret and dependency scans (§8.3)

\- Setup works from a clean clone

\- No personal data or restricted source content is exposed

\- Evaluation claims are supported by real results

\- Production configuration checklist above is satisfied



---



\# 25. Optional Stretch Work



Only consider these after B7:



\- Structured candidate profile

\- Full application tracker

\- Saved searches

\- Alerts

\- Resume PDF/DOCX extraction

\- pgvector

\- Semantic search

\- LLM-assisted ambiguity review

\- Multiple users

\- Email notifications

\- Object storage



Resume matching is not required for the project to be valuable or portfolio-worthy.



---



\# 26. v1 Data Architecture Direction



The v0 single-table design should later evolve only when justified.



Possible v1 models:



```text

Job

JobSourceRecord

Company

EmployerSource

Location

ClassificationRun

ClassificationEvidence

UserJobState

ClassificationFeedback

ImportRun

```



A normalized `Job` may eventually have multiple source records.



Do not perform this migration merely because it looks cleaner.



Do it when:



\- A second source exists

\- Duplicate grouping is required

\- Different sources refer to the same real posting

\- Classifier history needs to be retained

\- Multiple users require separate review state



---



\# 27. Portfolio Documentation



Maintain three levels of documentation.



\## 27.1 Product vision



```text

docs/product-vision.md

```



Contains:



\- Long-term problem

\- Target users

\- Product principles

\- Full feature direction

\- Non-goals



\## 27.2 Implementation roadmap



```text

docs/implementation-roadmap.md

```



Contains:



\- v0 and v1 stages

\- Current priorities

\- Completed phases

\- Deferred features



\## 27.3 v0 specification



```text

docs/v0-specification.md

```



Contains only:



\- Exact source

\- Exact fields

\- Exact rules

\- Exact workflows

\- Definition of done



This prevents the long-term vision from inflating the first milestone.



---



\# 28. Architecture Decisions



Document major decisions using ADRs when v1 begins.



Suggested ADRs:



```text

ADR-001: Use a modular monolith

ADR-002: Use Django as the backend

ADR-003: Use PostgreSQL from v0

ADR-004: Use deterministic classification first

ADR-005: Preserve uncertainty rather than hiding jobs

ADR-006: Use Django Admin for v0

ADR-007: Add Next.js only after workflow validation

ADR-008: Add PostGIS only after simple distance logic proves useful

ADR-009: Delay workers until manual imports become limiting

ADR-010: Use synthetic data for the public demo when necessary

```



Each ADR should include:



\- Context

\- Decision

\- Alternatives

\- Consequences

\- Revisit conditions



---



\# 29. GitHub Workflow



Each meaningful change should use:



1\. GitHub issue

2\. Small feature branch

3\. Implementation plan

4\. Code changes

5\. Tests

6\. Manual diff review

7\. Meaningful commits

8\. Pull request

9\. Passing CI

10\. Merge into `main`



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

research: evaluate first job source

chore: initialize Django and PostgreSQL

feat(jobs): add source-aware job model

feat(ingestion): import and update source jobs

feat(classification): separate required and preferred years

feat(location): calculate distance for supported cities

feat(admin): add daily review filters

test(ingestion): preserve review state on reimport

ci: run Ruff and pytest

```



Avoid:



```text

changes

stuff

working

fix

final

codex update

```



---



\# 30. Codex Rules



Codex should:



\- Work on one issue at a time

\- Inspect the repository first

\- Provide a plan for substantial changes

\- Follow `AGENTS.md`

\- Avoid unrelated refactors

\- Explain new dependencies

\- Add or update tests

\- Update documentation when behaviour changes

\- Run available verification

\- Report changed files

\- Report test results

\- State what could not be verified

\- Preserve user review state

\- Keep source-specific logic inside adapters

\- Keep classification logic outside management commands



Codex should not:



\- Build the full roadmap from one prompt

\- Add Next.js during v0

\- Add Celery during v0

\- Add PostGIS during v0

\- Suppress type errors

\- Disable tests

\- Commit secrets

\- Commit personal data

\- Use live API requests in normal tests

\- Invent source permissions

\- Hide failures with broad exceptions

\- Claim success without verification

\- Replace deterministic rules with an unexplained AI call



---



\# 31. Success Metrics



\## 31.1 v0 personal utility



Track:



\- New jobs found per import

\- Relevant jobs found per week

\- Jobs saved

\- Jobs applied to

\- Useful jobs not found as quickly elsewhere

\- Time required for daily review

\- Senior jobs incorrectly shown

\- Realistic jobs incorrectly hidden

\- Remote eligibility mistakes

\- Source that produced each useful lead



v0 succeeds when:



\- It is used for at least one real week

\- It finds at least one useful lead

\- Reviewing new jobs is faster than checking boards manually

\- The owner wants to continue using it



\## 31.2 v1 portfolio quality



v1 succeeds when:



\- Public demo works

\- README explains the problem clearly

\- Classifier metrics are published

\- Multiple adapters share a tested contract

\- PostGIS supports a real workflow

\- Deduplication is demonstrated

\- Source failures are handled

\- CI passes

\- Setup works from a clean clone

\- No personal information or secrets are committed

\- The project has meaningful issue and pull-request history



---



\# 32. README Structure



The final README should lead with the problem.



Suggested structure:



```text

1\. Problem

2\. Product demonstration

3\. What Breakwater does differently

4\. Architecture

5\. Data-source strategy

6\. Explainable classification

7\. Remote and hybrid eligibility

8\. Evaluation results

9\. Local setup

10\. Testing and CI

11\. Privacy and source compliance

12\. Known limitations

13\. Future work

```



Possible opening:



> Entry-level filters are often unreliable. A posting may be labelled junior while requiring several years of experience, or described as remote while accepting applicants from only one country. Breakwater collects permitted job data, separates required from preferred experience, evaluates Canadian remote eligibility, identifies nearby hybrid roles, and explains why each job is considered realistic, uncertain, stretched, or unsuitable.



---



\# 33. Resume Positioning



After v1 is implemented, a possible resume bullet is:



> Built and deployed Breakwater, a Django and Next.js job-discovery platform that normalizes postings from multiple sources, classifies early-career and remote-Canada eligibility using explainable versioned rules, and uses PostgreSQL/PostGIS for hybrid-distance filtering; added Docker, CI, automated tests, deduplication, and classifier evaluation.



Replace general wording with measured results when available.



Example:



> Evaluated the classifier against 200 labelled postings, preventing all tested senior-title roles from entering the strict-match queue while retaining 91% of manually identified early-career opportunities.



Do not publish metrics until they are real.



---



\# 34. Major Risks



\## 34.1 Weak source coverage



\*\*Risk:\*\* The application works technically but finds too few relevant jobs.



\*\*Mitigation:\*\* Validate sample data before implementing the full importer.



\## 34.2 Partial descriptions



\*\*Risk:\*\* A broad API only provides snippets.



\*\*Mitigation:\*\* Store content completeness and classify uncertain jobs as `UNCLEAR`.



\## 34.3 False negatives



\*\*Risk:\*\* Strict filters hide attainable jobs.



\*\*Mitigation:\*\* Keep `POSSIBLE`, `STRETCH`, and `UNCLEAR` queues visible.



\## 34.4 False positives



\*\*Risk:\*\* Too many irrelevant jobs make the tool annoying.



\*\*Mitigation:\*\* Save corrections, create regression tests, and tune rules from real use.



\## 34.5 Source restrictions



\*\*Risk:\*\* Public redistribution is not permitted.



\*\*Mitigation:\*\* Use official endpoints, document terms, preserve attribution, and use synthetic demo data.



\## 34.6 v0 becomes disposable



\*\*Risk:\*\* Quick code must be rewritten for v1.



\*\*Mitigation:\*\* Keep source adapters, classification modules, stable identifiers, PostgreSQL, tests, and evidence from the beginning.



\## 34.7 Overengineering



\*\*Risk:\*\* Infrastructure delays usefulness.



\*\*Mitigation:\*\* v0 uses only Django, PostgreSQL, Docker Compose, one source, and simple rules.



\## 34.8 Scope creep



\*\*Risk:\*\* Resume matching, AI, and alerts delay core search.



\*\*Mitigation:\*\* Keep them explicitly optional until after the deployed portfolio version.



\## 34.9 Unsafe handling of third-party content



\*\*Risk:\*\* Raw job-description HTML is rendered unsanitized, creating an XSS exposure once the tool has a real frontend or public demo.



\*\*Mitigation:\*\* Render as plain text by default; sanitize server-side if formatting is ever preserved (§8.3).



\## 34.10 Production misconfiguration



\*\*Risk:\*\* Django defaults meant for local development (DEBUG on, permissive `ALLOWED\_HOSTS`, a committed `SECRET\_KEY`) leak into the public demo.



\*\*Mitigation:\*\* Treat the B7 production-configuration checklist (§24, §8.3) as a hard completion criterion, not an afterthought.



---



\# 35. Final Project Principle



Breakwater does not need to contain every job.



It needs to make a focused set of opportunities more actionable.



The project succeeds when it:



\- Finds jobs the owner might otherwise miss

\- Makes daily review faster

\- Removes obvious senior and ineligible roles

\- Preserves realistic and uncertain opportunities

\- Explains every important classification

\- Improves from real user corrections

\- Measures its own quality

\- Demonstrates disciplined full-stack engineering



The final product promise is:



> Breakwater continuously discovers jobs relevant to an early-career candidate, combines remote-Canada and nearby hybrid opportunities, separates strong matches from stretches and uncertainty, and explains the evidence behind every result.



