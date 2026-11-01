# course-catalog-api

Course Catalog backend for Labs 4–7 of Advanced Web Technologies: FastAPI, SQLAlchemy 2.1, PostgreSQL and Alembic. In this workspace the standalone backend's root is `04-backend/`; Lab 6's independent SQL project is `../06-database/`. Lab 7 continues the existing backend rather than creating a second application.

## How to run

Use **Python 3.11+** and **PostgreSQL 16+**. SQLAlchemy is constrained to the required 2.1 series. Once, as the PostgreSQL administrator, create the teaching role and database, or reuse the ones created in Lab 6:

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog OWNER catalog_app;
```

From this project directory, for a **new, empty database**:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
alembic check
python check_db.py
python check_models.py
fastapi dev main.py
```

On Windows activate with `.venv\Scripts\Activate.ps1`. Adjust `DATABASE_URL` in `.env` for your server. An environment variable overrides the file. Run commands from the project root so settings find `.env` and Alembic finds `alembic.ini`. `.env` is ignored; `.env.example` contains only the public training address. `SQL_ECHO=true` enables SQL logging locally; its default is false, and it is intentionally absent from the example file.

Swagger: [http://localhost:8000/docs](http://localhost:8000/docs). In another terminal, with the same environment active, run `python try_errors.py`: on seeded data it prints **5 of 5 as expected** and exits nonzero if any status differs. The initial counts are **6 courses, 3 students, 6 enrollments**.

`seed.sql` is a destructive training reset: it runs TRUNCATE with RESTART IDENTITY and then all three inserts inside one transaction. It resets likes and deletes added students/enrollments. Repeating it is supported. Do not run it against production data. `change-me` is a teaching password; real credentials stay outside Git.

### Adopt an existing Lab 6 database

The initial migration creates the same three tables, constraint names, defaults and student index as Lab 6. An existing Lab 6 database already has these objects; applying 0001 to it gives DuplicateTable. Verify that it really matches the Lab 6 schema before marking it:

```bash
# Compare the existing schema with migration 0001 and Lab 6's schema.sql first.
alembic stamp 0001
alembic upgrade head
alembic check
python check_models.py
```

Use **0001**, not `stamp head`, when adopting Lab 6 with the final two-migration checkout: Lab 6 has no level column. Stamping head would incorrectly mark the level migration as applied. `stamp` records a version without running DDL and does not validate the schema. The original adoption and expected failure are recorded in [adoption.log](verification/adoption.log).

### Current local verification environment

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
