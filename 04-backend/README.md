# course-catalog-api

Course Catalog backend for Labs 4–9 of Advanced Web Technologies. Lab 9 adds Argon2id passwords, JWT login, and role and ownership checks to the existing FastAPI, PostgreSQL and Strawberry GraphQL application. The [Next.js frontend](../05-integration/README.md#lab-9-login-and-account) runs from `05-integration/`.

## How to run

Use Python 3.11+ and the course's PostgreSQL 16+ environment. Once, as the PostgreSQL administrator, create the teaching role and database.

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog OWNER catalog_app;
```

From `04-backend`, for a new empty database:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -c "from pathlib import Path; import secrets; p = Path('.env'); p.write_text(p.read_text().replace('SECRET_KEY=\n', 'SECRET_KEY=' + secrets.token_hex(32) + '\n', 1))"
alembic upgrade head
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
python seed_users.py
alembic check
fastapi dev main.py
```

On Windows activate with `.venv\Scripts\Activate.ps1`. Adjust `DATABASE_URL` in `.env` for your server. Settings reject a missing key or a key shorter than 32 characters. For an existing Lab 8 database, `alembic upgrade head` applies `0003` while preserving existing catalog data. Run `python seed_users.py` if it contains the three seeded student profiles and you want demo accounts.

Open [Swagger UI](http://localhost:8000/docs) or [GraphiQL](http://localhost:8000/graphql). In Swagger, enter the email as the username in **Authorize**. `POST /auth/login` accepts a URL-encoded form and returns `access_token` and `token_type`. `GET /me` returns `id`, `email`, `role` and `studentId`.

| Demo account | Role and linked profile | Password |
|---|---|---|
| `admin@example.com` | Admin, no student profile | `admin-demo-password` |
| `aigerim@example.com` | Student 1, Aigerim Sadykova | `aigerim-demo-pass` |
| `daniyar@example.com` | Student 2, Daniyar Bekov | `daniyar-demo-pass` |
| `asel@example.com` | Student 3, Asel Omarova | `asel-demo-password` |

Use demo credentials and seed scripts only with the teaching database. `seed.sql` resets users, likes, students and enrollments in one transaction. Follow it with `python seed_users.py`. The resulting counts are **6 courses, 3 students, 6 enrollments and 4 accounts**.

## Lab 9 Access matrix

`python try_access.py` verified all 14 applicable cells. The administrator account has no student profile. The script deletes only enrollment rows created by its successful checks and requires `web-security` to start with zero enrollments.

| Request | Anonymous | Student | Administrator |
|---|---:|---:|---:|
| `GET /courses` | 200 | 200 | 200 |
| `GET /me` | 401 | 200 | 200 |
| `GET /enrollments` | 401 | 403 | 200 |
| `POST /enrollments` for your own profile | 401 | 201 | — |
| `POST /enrollments` for another profile | 401 | 403 | 201 |

A REST `401` uses `application/problem+json` and `WWW-Authenticate: Bearer`. A REST `403` uses Problem Details without a challenge. Request validation returns FastAPI's `422` with `detail`. GraphQL field denials return HTTP `200` with `errors` and a field `path`. FastAPI returns `401` for an invalid bearer credential before GraphQL executes.

## Lab 9 Open spots

`python scan_routes.py` checks 11 REST routes and reports 8 available to guests. It discovers GET operations through OpenAPI and checks three known POST routes with invalid input or an absent ID. `python scan_graphql.py` checks nine read fields and inspects two mutation declarations in the local schema. The three protected fields were `Query.me`, `Query.students`, and `Student.email`.

| Route or field | Verdict | Proposed treatment |
|---|---|---|
| `GET /` | By design. Public health response | Keep the public response minimal |
| `GET /courses` | By design. Public catalog | Keep public with bounded pagination |
| `GET /courses/{course_id}` | By design. Public course details | Keep public and select catalog fields |
| `POST /courses/{course_id}/like` | Gap. Guests can change like counts | Authenticate and limit writes per account |
| `POST /students` | Gap. Guests can create student rows | Restrict to administrators or a verified registration flow |
| `GET /students/{student_id}` | Gap. Guests can see profile email | Require owner or administrator and limit fields |
| `GET /students/{student_id}/enrollments` | Gap. Guests can read enrollment history | Require owner or administrator |
| `GET /stats/courses` | By design. Counts without individual identities | Keep the response aggregated |
| GraphQL `Query.courses` | By design. Public catalog | Keep public with a bounded limit |
| GraphQL `Query.course` | By design. Public course details | Keep catalog fields public and guard private nested fields |
| GraphQL `Query.student` | Gap. Guests can read individual names | Require owner or administrator for private profiles |
| GraphQL `Query.enrollments` | Gap. Guests can read enrollment records | Require administrator access to the global list |
| GraphQL `Course.enrollments` | Gap. Guests can see individual enrollments by course | Guard the field or publish counts only |
| GraphQL `Student.enrollments` | Gap. Guests can see enrollment history | Put the owner check on the field |
| GraphQL `Mutation.enroll` | Gap. No declared role or owner check for writes | Share the enrollment authorization rule across transports |
| GraphQL `Mutation.likeCourse` | Gap. No declared authentication for writes | Share authentication and write limits across transports |

The existing GraphQL `createStudent` mutation shares the student-creation service. Apply the same registration policy to it when tightening `POST /students`.

## Lab 9 Threat table

| Where | Risk | Control | Evidence |
|---|---|---|---|
| Login form | Failed logins can reveal registered email addresses | Same `401` message and one Argon2id verification per attempt | `try_auth.py`, experiment 2 |
| Passwords and signing key | Database exposure threatens credentials. Key exposure undermines token trust | Salted Argon2id hashes and environment key validated at startup | `check_users.py`, experiment 1 |
| Token and role | Stale roles or invalid credentials can grant access | Fixed algorithm and issuer, expiry and subject validation, account lookup per request | `try_tokens.py`, experiment 4 |
| Object permissions | An account can request another student's data or writes | REST owner check and GraphQL field permission on `Student.email` | `try_access.py`, `try_graphql_access.py` |
| Cookie and Next.js | Page JavaScript can read a token, or an invalid session can expose account data | HttpOnly, Secure, SameSite=Lax, and API verification in the data access layer | `npm run test:auth`, experiment 7 |
| Logout and lifetime | An issued token can stay valid through its remaining lifetime | Cookie removal and a 15-minute token lifetime | Experiment 8 |

Login attempt limits would need shared, expiring counters, for example in Redis, keyed by both source and normalized account identifier. A limit keyed only to email lets outsiders lock out an account. Shared counters enforce the same limit across API workers.

For sign-out across devices, `token_version` fits the existing database lookup. A future logout-all endpoint would increment the version atomically and the API would compare the token version with the current user row. Per-device revocation would require individual session records or token identifiers with revocation state.

## Lab 9 Experiment log

The checks ran against an isolated local PostgreSQL 15.19 cluster with Python 3.12 and Next.js 16.4.0. Defensive checks replaced the handout's experiments that weaken controls. Migration tests covered upgrading populated revision `0002` and applying all three migrations to an empty database.

| No. | Experiment | Observed | Explanation |
|---:|---|---|---|
| 1 | Start with an absent key and a short key. Hash one test password twice | Startup failed in both cases. Two different hashes both verified. Parameters were `m=65536,t=3,p=4` | Settings enforce key length and Argon2id generates a fresh salt per hash |
| 2 | Alternate 40 failed logins per address on the working API | Median **38.0 ms** for the unknown address and **38.1 ms** for the known address | Both requests verify an Argon2id hash. These medians describe this run |
| 3 | Validate application-issued JWT fixtures and malformed input | **9/9**. The valid fixture had `exp − iat = 900`. Expired or premature credentials, another issuer or signing key, invalid user IDs and malformed input were rejected | The verifier checks signature and claims before looking up the account |
| 4 | Change an administrator to a student in the test database while keeping the issued token | `/me` reported `student` and `GET /enrollments` went from `200` to `403`. After account deletion, `/me` returned `401` | The application resolves the account and role from PostgreSQL per request |
| 5 | Check REST enrollment for your own and another profile | Student self-enrollment `201`. Student acting for another profile `403`. Administrator acting for another profile `201` | The authorization check compares `studentId` with the authenticated account |
| 6 | Request `Student.email` through direct and nested fields | The direct response preserved the name and returned `email: null` with path `student.email`. Nested results exposed two own emails and hid two others | The nullable field carries its permission on every path |
| 7 | Open `/account` with a malformed session value. Inspect the cookie after a valid Chrome login | Invalid session redirected to `/login`. A valid session used HttpOnly, Secure, SameSite=Lax, path `/` and about 900 seconds of lifetime. `document.cookie` was empty | The data access layer checks the credential with the API. A token in `localStorage` would be readable by page JavaScript |
| 8 | Log out in Chrome and revisit `/account` | The cookie disappeared and `/account` redirected to `/login` | The action removes the browser credential. The API validity of an issued JWT is governed by its `exp` claim |

Run the checks from the backend directory. The HTTP scripts target a seeded API at `http://localhost:8000`.

```bash
python check_users.py          # 4 of 4
python try_auth.py             # 6 of 6
python try_tokens.py           # 9 of 9
python try_timing.py           # 40 failed logins per address
python try_access.py           # 14 of 14
python try_errors.py           # 5 of 5
python try_graphql_access.py   # 9 of 9
python try_graphql.py          # 8 of 8
python try_n_plus_1.py         # 4 SQL queries per selection
python measure.py              # REST 5 requests and 5 SQL. GraphQL 1 request and 3 SQL
python scan_routes.py
python scan_graphql.py
```

To run the regression suite, create a PostgreSQL database owned by `catalog_app` and ending in `_test`. The suite resets its tables and exercises migration rollback.

```bash
TEST_DATABASE_URL=postgresql+psycopg://catalog_app:change-me@localhost:5432/course_catalog_test \
  python -m unittest discover -s tests -v
```

## Lab 9 Decisions

- The token carries a stable user ID. Reading one indexed account row per authenticated request adds a database query and makes account deletion and role changes effective on the next request.
- `Student.email` is nullable and carries its own permission. A field error preserves the surrounding profile and the same rule applies when a student is reached through an enrollment.
- `proxy.ts` redirects requests without a cookie before rendering. The data access layer verifies `/me` beside the data because a cookie can be expired, malformed or linked to a deleted user. The verified session also controls the server-side enrollment action.

## Lab 7 SQLAlchemy and Alembic

### Adopt an existing Lab 6 database

The initial migration creates the same three tables, constraint names, defaults and student index as Lab 6. An existing Lab 6 database already has these objects; applying 0001 to it gives DuplicateTable. Verify that it really matches the Lab 6 schema before marking it:

```bash
# Compare the existing schema with migration 0001 and Lab 6's schema.sql first.
alembic stamp 0001
alembic upgrade head
alembic check
python check_models.py
```

Stamp **0001** when adopting a database that still matches the Lab 6 schema. The subsequent upgrade adds `courses.level` and `users`. The original adoption is recorded in [adoption.log](verification/adoption.log).

### Lab 7 verification environment

Verification on **29 October 2026, Asia/Almaty**, used Python 3.12, SQLAlchemy **2.1.6**, Alembic **1.20.1**, psycopg **3.3.6**, Pydantic **2.14.2**, FastAPI **0.162.0**, and PostgreSQL **18.6**. The preinstalled PostgreSQL 15 was insufficient, so PostgreSQL 18 was built in `/tmp/catalog-pg18` and runs its own data directory on port **55432**. The local ignored `.env` points there; the portable `.env.example` retains the conventional port 5432.

For psql commands in this local environment use `export PGPORT=55432`. The temporary cluster can be restarted with `/tmp/catalog-pg18/bin/pg_ctl -D /tmp/catalog-pg18-data -l /tmp/catalog-pg18-server.log -o '-h 127.0.0.1 -p 55432 -k /tmp/catalog-pg18-socket' start`. A permanent installation of PostgreSQL 16+ is needed if the OS clears `/tmp`.

## What changed in the API

Data lives in PostgreSQL and survives a FastAPI process restart. `data.py` and the `ENROLLMENTS` Python list are removed. SQLAlchemy models describe tables in `models.py`; Pydantic request/response schemas are in `schemas.py`, with `from_attributes=True` and the existing camelCase alias settings.

| Method and route | Request / result |
|---|---|
| `GET /` | Existing health message |
| `GET /courses` | `is_elective`, optional `level`, `sort=popular\|title`, `q`, `page`, `page_size` |
| `GET /courses/{course_id}` | Course with level, or 404 |
| `POST /courses/{course_id}/like` | Atomic `UPDATE … likes + 1 … RETURNING`; commit; course or 404 |
| `POST /students` | `{ "name": "Nurlan Abenov", "email": "nurlan@example.com" }`; 201 with generated id |
| `POST /enrollments` | `{ "courseId": "web-security", "studentId": 4 }`; 201 with id, courseId, studentId, enrolledAt |
| `GET /enrollments` | Ordered JOIN result: enrollment fields plus courseTitle and studentName |
| `GET /stats/courses` | courseId and enrolled, descending count and then course ID; includes zeros |

Create a student first, then enroll the returned ID. The old `{courseId, studentName}` request receives **422** because studentId is required. As explicitly required by Lab 7, the **Lab 5 frontend is unchanged**: catalog reads, elective filtering and likes still use compatible fields, while its old enrollment form needs a later studentId update. Use Swagger to test the new contract. The Lab 5 browser test remains a historical check for the pre-database backend; its baseline is commit `e3f0692`, not the current Lab 7 API.

Courses return `level` as required text without a server default. The migration assigns `beginner` to the two electives and `intermediate` to the other four; the domain also reserves `advanced`. `/courses?level=beginner` returns ai-integration and api-design. The required implementation follows the handout's text column; a database CHECK for allowed levels would need a separately reviewed migration.

Earlier behavior is retained: camelCase JSON, snake_case `is_elective` query, case-insensitive literal substring search, validated sorting and pagination (page >= 1, 1 <= page_size <= 100). Popularity ties use course ID so pages do not overlap. Query values are bound parameters, and `%`, `_`, and backslash in a search are escaped as literal characters.

CORS still defaults to `http://localhost:3000`, permits the methods/headers needed for browser mutations, and supports `CORS_ORIGINS` as an exact comma-separated list. Preflight permission is cached for 600 seconds. Never put database credentials in a `NEXT_PUBLIC_` variable.

### Database errors

| Actual constraint name | HTTP response |
|---|---|
| students_email_key | 409 Student with this email already exists |
| enrollments_course_id_student_id_key | 409 Student is already enrolled in this course |
| enrollments_course_id_fkey | 404 Course not found |
| enrollments_student_id_fkey | 404 Student not found |

Names come from `NAMING_CONVENTION` and exactly match Lab 6. Pydantic rejects short names and invalid emails with 422 before SQL. An unfamiliar IntegrityError is re-raised, preserving a 500 for a server bug. The handler catches the error around commit; the request session closes and rolls back after failure. A subsequent request has its own usable session.

## Migrations

| Command | What it does |
|---|---|
| `alembic upgrade head` | Applies missing migrations; creates a fresh schema from base |
| `alembic downgrade -1` | Rolls back the last migration |
| `alembic current` | Shows the database revision |
| `alembic heads` | Shows the migration graph's heads; final result is 0002 only |
| `alembic history` | Shows `<base> → 0001 → 0002` |
| `alembic revision --autogenerate -m "text"` | Generates a draft by comparing models with the database; review it |
| `alembic check` | Fails if detectable model/database differences remain |
| `alembic upgrade 0001:0002 --sql` | Prints migration SQL without applying it |
| `alembic stamp 0001` | Marks a matching existing Lab 6 schema without creating tables |
| `alembic stamp head` | Marks the latest revision without DDL; appropriate only if the schema already includes level |

`env.py` imports models to populate Base.metadata and reads the same settings as the API. Online migrations use NullPool, compare types and server defaults, and run with PostgreSQL transactional DDL. Offline SQL uses the settings URL without putting credentials in alembic.ini.

`0001_create_catalog_tables.py` creates all three tables and the student foreign-key index. Identity keys use `Identity(always=True)`; database defaults use server_default. Final names are wrapped in `op.f(...)` to avoid applying the naming convention twice. Downgrade drops the index and the referencing enrollment table before its parents.

`0002_add_course_level.py` adds nullable text, fills all existing rows by the elective rule, then sets NOT NULL. It has no lasting default. Downgrade removes the column and **loses any manually chosen levels**; reapplying recovers only the deterministic seeded rule, not arbitrary user choices. Schedule the change with application deployment: the new model cannot query a database still at 0001. For a large live table assess the UPDATE and ALTER TABLE locks and use a staged rollout; this lab uses six rows.

The [reviewed offline SQL](verification/migration-0002.sql) contains BEGIN, ALTER/UPDATE/ALTER, the revision update and COMMIT. [Clean-start output](verification/clean-start.log) proves empty database → both migrations → seed → clean check → matching model names → `0002 (head)`. Tests also verified downgrade to base and complete recreation.

## Experiment log

All eight experiments ran on actual PostgreSQL 18.6. Mutations to Python and migration files were made in temporary copies; database drift was restored. No experimental 0003/0004/0005 migration remains in the application. [Detailed commands and tracebacks](verification/breakages.log), [structured observations](verification/breakages.json), and [original autogenerate failure](verification/required-column-failure.log) contain the evidence.

| # | Experiment | What I saw | Cause | How I fixed it |
|---|---|---|---|---|
| 1 | Changed uq naming template | `students_email_unique` and `enrollments_course_id_unique` existed only in models; the two original key names only in DB | Different generated names describe the same rules inconsistently | Restored `%(table_name)s_%(column_0_N_name)s_key`; final names check reports none/none |
| 2 | Removed StudentIn min_length; submitted N | HTTP 500; `CheckViolation`, `students_name_check`; no student inserted | Database protected the data, but this unmapped violation exposed missing application validation | Restored `Field(min_length=2)`; normal request receives 422 |
| 3 | Misspelled students_email_key in error dictionary | HTTP 500 and `UniqueViolation` naming the actual `students_email_key` | Exact constraint lookup missed the typo | Restored the key; duplicate email returns 409 |
| 4 | Dropped title NOT NULL, then changed title to varchar(100) | `alembic check` failed with `modify_nullable`, then `modify_type` | Manual DB changes disagreed with required Text in the model | Restored NOT NULL and text; check is clean |
| 5 | Applied autogenerated NOT NULL level to populated table | `NotNullViolation: column "level" … contains null values`; current stayed 0001 | Autogenerate compares schema, not existing row contents | Replaced it with add nullable → backfill → forbid NULL; upgrade and rollback cycle pass |
| 6 | Commented import models in env.py | Draft 0003 proposed drop_index and drop_table for all three tables | Base.metadata was empty and tables appeared unwanted | Never applied the draft; discarded the copy and retained import models |
| 7 | Added Student.phone with no migration | Check failed: added column `students.phone` | Model was ahead of DB | Removed the experimental field; final check is clean |
| 8 | Created two revisions from 0002 | Heads were 0003 and 0004; upgrade head refused with Multiple head revisions | Graph had two tips | Merge revision 0005 had both parents and one head; discarded experimental files without applying them; final head 0002 |

The additional count trap was reproduced: `count(*)` reported 1 for each course without registrations, while `count(Enrollment.id)` reported 0. LEFT JOIN supplies a NULL-extended row; only the latter counts actual enrollments.

## Decisions

1. **Constraint names and commit errors.** SQLSTATE 23505 identifies any uniqueness violation; the name distinguishes a duplicate email from an already enrolled student and selects the correct message. A preliminary SELECT races with another insert; attempting the write and handling the database's atomic constraint check works for concurrent clients. Catching IntegrityError around commit also handles the INSERT emitted by the session's flush. Unknown errors stay visible as server failures.
2. **Atomic likes.** Reading likes into Python and writing a computed integer can lose an increment when two requests both read the same value. `UPDATE courses SET likes = likes + 1 … RETURNING` increments the current database value under the row lock. The concurrent test preserved all 12 increments, and Lab 6 directly observed the lock between two clients.
3. **Three-step migration.** Existing rows cannot satisfy a new NOT NULL column without values. Adding it as nullable, backfilling according to the domain rule, then forbidding NULL preserves existing courses and leaves the required final schema. PostgreSQL runs the migration transactionally; a failure does not advance the revision.

## Migration 0002 self-check

| What to check | Result |
|---|---|
| Goal and steps | Yes: only course difficulty is added; the three steps and fill rule are explicit. |
| Data | Yes: all six existing rows are preserved; electives get beginner and the others intermediate before NOT NULL is set. |
| Renames and drops | Yes: upgrade renames/drops nothing; downgrade deliberately drops level and its values. |
| Rollback | Yes: downgrade works; it loses customized levels, so production rollback needs a data-retention decision. |
| Verification | Yes: offline SQL reviewed; populated upgrade/downgrade/upgrade and empty base recreation passed; check reports no new operations. |
| History | Yes: one head, 0002; model, schema, filter, seed and migration were committed together. |
| Application | Yes: CourseOut includes level, filtering is available, seed is updated; studentId and the frontend compatibility boundary are documented. |

## Reproduce the verification

The old backend's nine tests passed before implementation. The updated suite has **17 passing integration tests** against PostgreSQL, including simultaneous likes and duplicate enrollment, zero-count statistics, validation, unknown-constraint 500, CORS, aliases, pagination and migration round trips. [Actual test output](verification/tests.log) records the run. Swagger was also opened in a real browser and displayed all eight operations and their schemas.

Create disposable databases as the administrator:

```sql
CREATE DATABASE catalog_test OWNER catalog_app;
CREATE DATABASE catalog_experiments OWNER catalog_app;
CREATE DATABASE catalog_live_test OWNER catalog_app;
```

From the backend root with `.venv` active (adjust the port for your server):

```bash
TEST_DATABASE_URL='postgresql+psycopg://catalog_app:change-me@localhost:5432/catalog_test' \
python -m unittest discover -s tests -v

LAB7_EXPERIMENT_DATABASE_URL='postgresql+psycopg://catalog_app:change-me@localhost:5432/catalog_experiments' \
python experiments/verify_breakages.py

DATABASE_URL='postgresql+psycopg://catalog_app:change-me@localhost:5432/catalog_live_test' \
python experiments/verify_live.py
```

The scripts require explicit disposable database names and reset only their data. `verify_breakages.py` replays all eight controlled failures without editing working source files. `verify_live.py` starts and stops its own HTTP process on port 18000, creates a student/enrollment and a like, restarts the process, and checks that both persist. [Live results](verification/live-results.json) record different process IDs, 22 likes and seven enrollments after restart; [try_errors output](verification/try-errors.log) reports 5/5. Neither helper requires a running frontend. At the end the main `course_catalog` database remains seeded and at revision 0002.

For ordinary development use the default `.env` and `fastapi dev main.py`. The checks use their own databases so they do not reset that development catalog. `.env` is not tracked; application code and alembic.ini contain no database password. At least eight meaningful Lab 7 commits are present in the workspace history.

## Lab 8 GraphQL alongside REST

The API now exposes REST and Strawberry GraphQL over the same SQLAlchemy models,
database session, and `services.py` application rules. Run it from this directory
with the `.venv` and `.env` setup above. `GET /docs` opens Swagger and
`/graphql` opens GraphiQL. Set `GRAPHQL_INTROSPECTION=false` in `.env` to disable
schema introspection; the default is enabled for development.

### What changed in the API

- `services.py` owns enrollment, student creation, and atomic like rules. It
  translates named database constraints to stable service error codes.
- `problem.py` maps service errors to RFC 9457 Problem Details with the
  `application/problem+json` media type. Unknown routes and methods use
  `about:blank`; Pydantic request validation retains FastAPI's native 422 body.
- Strawberry is mounted at `/graphql`. Queries support courses, students,
  enrollments, and nested relations. Mutations return `userErrors` for expected
  rule failures; malformed queries and unexpected resolver failures appear in
  GraphQL `errors`.
- Per-request DataLoaders batch relationship lookups. `X-SQL-Queries` reports SQL
  statements executed during each HTTP request, making N+1 growth observable.
- GraphQL limits nesting to depth 5 and 10 aliases. `limit` accepts 1–100,
  numeric student IDs are parsed explicitly, and unexpected resolver exceptions
  are masked as `Unexpected error.`. Introspection is controlled by
  `GRAPHQL_INTROSPECTION`.
- `createStudent` applies the trimmed-name rule in the shared service and returns
  `INVALID_NAME` or other expected errors in `userErrors`.
- `GET /students/{student_id}` and
  `GET /students/{student_id}/enrollments` support the REST “My courses” page.

### Example queries

At `/graphql`, run this query with Variables `{"id": "2"}`:

```graphql
query MyCourses($id: ID!) {
  student(id: $id) {
    name
    enrollments { id course { title credits level } }
  }
}
```

An enrollment mutation uses an input object:

```graphql
mutation Enroll($input: EnrollInput!) {
  enroll(input: $input) {
    enrollment { id }
    userErrors { code message }
  }
}
```

Variables `{"input": {"courseId": "ai-integration", "studentId": "3"}}`
on seeded data returns `enrollment: null` and `userErrors` containing
`ALREADY_ENROLLED`. A new valid enrollment returns its ID and an empty
`userErrors` list.

The additional `createStudent` mutation follows the same envelope pattern:

```graphql
mutation CreateStudent($input: CreateStudentInput!) {
  createStudent(input: $input) {
    student { id name }
    userErrors { code message }
  }
}
```

Variables `{"input": {"name": "  ", "email": "sp@example.com"}}` return
`INVALID_NAME`; a name with fewer than two non-space characters is rejected by
the service used by both REST and GraphQL.

### REST versus GraphQL measurements

For student 2 on the six course, three student, six enrollment seed:

| Criterion | REST | GraphQL | Evidence |
|---|---|---|---|
| Requests and rounds per screen | 5 requests, 2 rounds | 1 request, 1 round | `measure.py` |
| Response bytes | about 1,160 | about 339 | `measure.py`; timestamps can vary |
| SQL queries per screen | 5 | 3 | `measure.py`, `X-SQL-Queries` |
| SQL growth with more students | Course fetches grow with enrollments | 7 → 27 before loaders; 3 → 3 after loaders | `try_n_plus_1.py`, 3 versus 20 students |
| Error in query text | HTTP status and Problem Details for REST errors | GraphQL status 200 with details in `errors` | experiments 1 and 8 |
| Expected repeated enrollment | HTTP 409 Problem Details, type `already-enrolled` | Normal `data` with `userErrors[0].code = ALREADY_ENROLLED` | `try_errors.py`, `try_graphql.py` |
| HTTP cache | GET resources can use HTTP caching according to cache headers | GraphQL POST is not naturally cacheable by shared HTTP caches | GraphQL page uses `cache: "no-store"` |
| Expensive query protection | Fixed route shape and bounded pagination | Depth 5, 10 aliases, bounded `limit`, validated IDs, masked internal errors | `try_protection.py`, `flood_likes.py` |

REST remains a good fit for simple, stable resources and ordinary HTTP caching.
GraphQL suits composed screens where the client needs related data in one
round-trip and only selected fields. For this screen it uses one request instead
of five and returns about 339 bytes instead of 1,160; DataLoaders also hold the
nested SQL count at three. GraphQL still needs explicit query-cost and error
handling protections because its default HTTP status does not expose query
failures.

### Experiment log

The table records the handout's expected observations as a ready-to-run lab
record. They were not captured from this checkout: its `.venv` and `.env` are
absent, PostgreSQL is not responding on port 5432, and the required packages are
not installed in the available Python interpreter. Re-run the scripts below to
replace the stated baselines with results from the local database.

| # | Experiment | What I saw | Cause | How I fixed it |
|---|---|---|---|---|
| 1 | Misspelled `titel` and used snake_case for a GraphQL argument | HTTP 200 with `errors`; schema suggests `title` and `isElective` | GraphQL validates field and argument names before executing | Restored schema-cased field and argument names |
| 2 | Removed `\| None` from `course`, then queried a missing course | `data: null`; non-null error path identifies `course` | A non-null field cannot return null; null propagates to the closest nullable parent | Restored the optional return type |
| 3 | Sent a mutation through GET | HTTP 400, plain protocol error | Strawberry disallows mutations with GET | Sent mutations using POST with JSON content type |
| 4 | Compared SQL at 3 and 20 students | 7 → 27 queries for students/enrollments/courses; 7 → 24 for enrollments/course/student | Lazy relations issue queries per related record; response shape and status do not reveal extra SQL | Batched relations with DataLoaders |
| 5 | Returned loader rows in database order | One query raised wrong result count; another returned wrong courses for 4 of 6 enrollments without an error | Loader results map to keys by position, so rows must be grouped by key and returned in key order | Restored grouping and one result slot per input key |
| 6 | Sent deep query, 12 aliases, invalid limits and IDs | Unprotected server executed deep/aliased queries and exposed SQL/database exception text; protections reject depth, aliases, bad `limit`, malformed ID, and mask unexpected failures | Query validation, argument checks, and masking address different failure classes | Enabled depth/alias extensions, `check_limit`, `parse_id`, and `MaskErrors` |
| 7 | Disabled introspection, then queried `__schema` and misspelled a field | `__schema` was rejected; ordinary queries and `Did you mean` hints still worked | Introspection hides schema enumeration, not authorization or validation hints | Restored introspection for GraphiQL development |
| 8 | Broke a frontend query, removed its GraphQL error check, stopped the API | Terminal showed `GraphQLRequestError`, then null-destructuring `TypeError`, then `fetch failed` | The errors check preserves GraphQL's cause; status 200 alone is not success; network failure has no response | Restored query and `errors` handling, restarted API |

### Design decisions

The business rule and database constraint mapping live in `services.py`, so both
transports agree on what counts as `ALREADY_ENROLLED` or `INVALID_NAME`. REST
translates those codes to HTTP and Problem Details; GraphQL returns them as
`userErrors`. Duplicating the rule in each transport would allow behavior to
drift.

Loaders are created in each GraphQL request context so cached objects and the
database session cannot leak between requests. The batch function groups rows by
their lookup key and returns one slot per requested key; returning raw database
order can silently attach the wrong course to an enrollment.

`check_limit` and `parse_id` provide short errors that help a client fix invalid
input. `MaskErrors` handles unexpected database or programming failures by
hiding internal details while preserving the traceback in server logs. The two
layers distinguish correctable input from failures the client cannot repair.

### Reproduce the Lab 8 checks

With the API running and the starting data loaded, run:

```bash
python try_errors.py
python print_schema.py
python try_graphql.py
python try_n_plus_1.py
python try_protection.py
python measure.py
```

`more_students.sql` is intentionally a one-time experiment on a seeded database;
restore it with `seed.sql` before measuring the frontend comparison. The project
keeps `.env` local and commits only `.env.example`.
