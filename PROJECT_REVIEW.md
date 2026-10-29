# Project review and verification of Labs 6 and 7

Reviewed on 29 October 2026, Asia/Almaty. Baseline: `e3f0692`, the merged Lab 5 integration. The working tree was clean before implementation. Both supplied DOCX assignments were read as requirements for the two labs; their example commands and external submission instructions were evaluated separately from the user's request to implement the work.

## Existing structure and behavior

| Project | Structure and behavior reviewed | Consequence for Labs 6 and 7 |
|---|---|---|
| 01 GitHub Explorer | Static HTML/CSS/JS; GitHub fetch, username validation, language filtering, star/name sorting, localStorage | Independent earlier exercise; no backend or database to reuse |
| 02 Course Catalog | Next.js App Router, local Course type and six mock records, generateStaticParams, awaited params, notFound/loading, local likes | Establishes URL slugs, server/client separation and camelCase UI fields; its older course values differ from the later API |
| 03 Tailwind | Same older mock catalog, responsive grid, cards/buttons/badges, active navigation and system dark colors | Presentation baseline for Lab 5; unrelated to the database migration |
| 04 Backend before Lab 7 | FastAPI, Pydantic aliases, six standard handout courses in data.py, pagination/search/sort, in-memory likes/enrollments, CORS | Canonical six seed records and existing API behavior; this is the application that Lab 7 must evolve |
| 05 Integration | Server fetches with no-store and HTTP checks, SWR browser filter, real like POST, enrollment form, error/retry and loading UI, CORS fault journal | Browser consumers must retain camelCase; studentName enrollment is intentionally retired in Lab 7 without editing the frontend |

Nine original backend integration tests passed before any behavior change. The new tests preserve the applicable assertions and replace the old in-memory/enrollment expectations with the required PostgreSQL contract. The old browser test belongs to the Lab 5 baseline because it imports the removed in-memory data and expects studentName; it was not falsely reported as a passing Lab 7 test. Directories 01, 02, 03 and 05 are unchanged.

## Implementation choices

Lab 6 is an independent SQL project in `06-database`, matching the repository's numbered directory convention. Its schema has no `level` column: that is added by Lab 7. Tests use separate databases, so rebuilding Lab 6 cannot accidentally remove Lab 7's migrated schema.

Lab 7 stays in `04-backend` as the assignment explicitly continues the existing API. Pydantic schemas were moved with Git before SQLAlchemy models were added. No extra service/repository abstraction was introduced for these small CRUD routes. Each request receives its own SQLAlchemy session. Parameters are bound, likes increment in SQL, integrity errors are mapped by the actual constraint name, and unknown violations remain visible as 500 errors.

The three existing query behaviors were retained: case-insensitive literal title search, validated pagination and validated sorting. Ordering now has an explicit ID tie-breaker. CORS remains configurable as in Lab 5. Database credentials come only from settings; `.env` is ignored, and the committed example contains the assignment's public training password.

## Lab 6 requirement mapping

| Required item | Implementation and evidence |
|---|---|
| PostgreSQL 16+, non-superuser owner, main and experiment databases | PostgreSQL 18.6; catalog_app owns the isolated training databases; server version recorded in verification/experiments.json |
| Three tables, exact types and required columns | schema.sql; bigint ALWAYS identities, text slugs, timestamptz enrollment time |
| Defaults, three CHECKs, email/pair uniqueness, two delete rules | schema.sql; ten real rejection cases and a cascade in experiments/verify.py |
| Exact 6/3/6 seed from the later backend | seed.sql; initial/final counts and clean-start output |
| Nine mandatory route-query variants | queries.sql: 1/1b, 2/2b, 3/3b, 4, 5, 6; both modifying groups roll back |
| Repeatable queries and correct zero counts | Two complete runs in verification/clean-start.log; count(e.id) retains empty courses |
| Ten violations with SQLSTATE, names and hypothetical HTTP codes; cascade | README violation table; verification/experiments.json includes actual diagnostic messages |
| Why CHECK is needed in addition to Pydantic | README, Constraint violation log |
| Student FK index; large dataset; before/after plans and three-run timing | schema.sql, experiments/idx_data.sql, README and verification/experiments.json |
| Two-window rollback and committed visibility | Two real connections; errors 23503/25P02 and observer [0,0] → [1,1] |
| ER diagram, three design answers, seven-row self-review and clean start | README and verification/clean-start.log |
| At least six meaningful commits | Six incremental Lab 6 commits before final packaging, beginning accfcc8 |
| GitHub standalone submission | Prepared locally; external publication has not been performed |

Bonus tasks 1–4 are implemented and verified: normalization anomalies, lost update/row lock, parameterized SQL injection example, and LEFT JOIN/HAVING queries. The optional live email-format rule from bonus 5 is not part of the final Lab 6 schema, keeping it identical to the initial schema required by Lab 7.

## Lab 7 requirement mapping

| Required item | Implementation and evidence |
|---|---|
| Python 3.11+, SQLAlchemy 2.1, psycopg, Alembic, pydantic-settings | requirements.txt; actual dependency versions documented and pip check passed |
| Required settings URL, optional SQL echo, ignored .env, example URL | config.py, .gitignore, .env.example; no URL/password in main.py, db.py or alembic.ini |
| Engine, Base, naming/type conventions and per-request session | db.py; check_models.py reports none/none |
| SQLAlchemy tables, server defaults, identities, relationships and passive deletes | models.py; names match Lab 6 and Alembic |
| Course routes with filters/order/pages and UPDATE RETURNING like | main.py; 17-test suite includes concurrency, literal search and stable pagination |
| Student/enrollment creation, JOIN details and zero-count statistics | main.py and schemas.py; tests cover 201, timestamps, names/titles, seeded statistics |
| Four constraint-name HTTP mappings; unknown violations remain 500 | CONSTRAINT_ERRORS and raise_http_error; tests plus live try_errors.py 5/5 |
| Fresh 0001 from empty scratch; adopt existing Lab 6 schema with stamp | Generated on scratch and check passed; verification/adoption.log records DuplicateTable, stamp 0001 and clean check |
| Exactly two final migrations and one head | alembic/versions/0001 and 0002; current/heads 0002 and check clean |
| Required level in model/response/filter/seed, backfill and rollback | 0002 three-step migration; failed autogenerated attempt recorded before correction; populated round trip and fresh base recreation passed |
| Eight controlled failures with causes and fixes | experiments/verify_breakages.py, README and verification/breakages.log/json |
| Clean database start and actual API process restart | verification/clean-start.log and experiments/verify_live.py; two distinct process IDs and persisted mutations |
| Three decisions and seven-row migration checklist | README |
| At least eight meaningful commits | Ten incremental Lab 7 commits before final packaging, beginning 71dbbbe |
| Same backend GitHub submission, frontend unchanged | Existing backend continued locally; no remote publication performed |

## Verification results and limits

- Original backend baseline: 9/9 tests passed.
- Lab 6: ten constraint errors matched diagnostics; cascade and rollback passed; final row counts 6/3/6; both query-file runs completed without errors.
- Lab 6 index: 50,000-row sequential scan changed to a bitmap index scan; raw EXPLAIN ANALYZE output and three timings per condition are retained.
- Lab 7: 17/17 PostgreSQL integration tests passed, including simultaneous updates and duplicate enrollment.
- All eight deliberate Lab 7 failures were observed; temporary source copies and experimental revisions were discarded. The working migration directory contains only 0001 and 0002.
- A real Uvicorn process was stopped and replaced by a new one. The like remained 22 and the newly created enrollment remained present; try_errors.py returned 5/5.
- Fresh migrations, seed, model-name check, Alembic check/current/heads and dependency check passed. Main course_catalog is reset to the initial 6/3/6 at revision 0002.
- PostgreSQL 18 runs in a temporary directory on port 55432. The preinstalled PostgreSQL 15 was left unchanged. The temporary server/data may need rebuilding after OS cleanup; permanent setup instructions require PostgreSQL 16+.
- GitHub publication, repository URLs and live GitHub rendering of the Mermaid diagram are external submission steps. They are not claimed complete. The local implementation, reports, evidence and incremental Git history are ready for review.
