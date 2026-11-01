# course-catalog-db

Lab 6 of Advanced Web Technologies: a normalized PostgreSQL catalog and verified SQL experiments. In this workspace the standalone project's root is `06-database/`. The six courses come from the backend after Labs 4–5, rather than the older frontend mock catalog. Lab 6 does not change application code; Lab 7 continues separately in `../04-backend/`.

## How to run

Use PostgreSQL **16 or newer** and UTF-8 files. As the server administrator, create the teaching role and databases once:

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog OWNER catalog_app;
CREATE DATABASE idx_demo OWNER catalog_app;
CREATE DATABASE norm_demo OWNER catalog_app;
```

From this directory, enter the teaching password when prompted:

```bash
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f schema.sql
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f queries.sql
```

`schema.sql` deliberately drops the three training tables and their data. It is safe to repeat only in a disposable catalog. Run schema and seed together to restore the initial 6 courses, 3 students and 6 enrollments. `seed.sql` alone expects empty tables. `queries.sql` can run repeatedly: its writes roll back, although identity sequences still advance. Do not run Lab 6's schema against the migrated Lab 7 database; use a separate database such as `lab6_verify` when retaining both results.

For another PostgreSQL port set `PGPORT` before these commands. Verification on 29 October 2026 used an isolated PostgreSQL 18.6 on port **55432**, because the computer's existing PostgreSQL 15 does not satisfy the assignment. The installed service was left unchanged. `change-me` is a public teaching password, not a production secret.

## Schema

```mermaid
erDiagram
    COURSES ||--o{ ENROLLMENTS : "course enrollments"
    STUDENTS ||--o{ ENROLLMENTS : "student enrollments"
    COURSES {
        text id PK "course slug"
        text title
        text description
        integer credits
        boolean is_elective
        integer likes
    }
    STUDENTS {
        bigint id PK
        text name
        text email UK
    }
    ENROLLMENTS {
        bigint id PK
        text course_id FK
        bigint student_id FK
        timestamptz enrolled_at
    }
```

The diagram source is also available as [er-diagram.mmd](er-diagram.mmd).

![Course catalog ER diagram](er-diagram.png)

The vector version is also available as [er-diagram.svg](er-diagram.svg).

Courses and students have a many-to-many relationship through enrollments. Each enrollment has exactly one course and one student; the pair `(course_id, student_id)` is unique. Course and student facts are stored once in their own tables.

All columns are required. Defaults are `false` for electives, `0` for likes, and `now()` for enrollment time. Credits must be positive, likes nonnegative, and student names at least two characters. Student and enrollment IDs use `bigint GENERATED ALWAYS AS IDENTITY`.

## Design decisions

- Course IDs are readable text slugs shared with URLs and the previous API. Renaming a slug affects references and external links. Student IDs are generated bigint values: they are compact, stable when names change, and avoid using personal information as keys; a separate unique email identifies a student's address.
- `ON DELETE RESTRICT` prevents removing a course with existing registrations. `ON DELETE CASCADE` removes a deleted student's registrations, which have no meaning without that student. The database enforces both rules for every client.
- `timestamptz` stores an unambiguous instant and displays it in the session's time zone; plain `timestamp` does not identify an instant without additional context. `text` avoids an arbitrary length limit and does not carry a performance penalty compared with `varchar(n)` in PostgreSQL; domain length rules belong in explicit constraints.

## Constraint violation log

These commands ran against real PostgreSQL 18.6. In psql, use `\set VERBOSITY verbose` or `\errverbose` to see SQLSTATE and diagnostics. The executable cases, actual messages, column names and SQLSTATEs are in [experiments/verify.py](experiments/verify.py) and [verification/experiments.json](verification/experiments.json).

| # | Violation | SQLSTATE | Constraint or column | Hypothetical API response |
|---|---|---|---|---|
| 1 | NULL in courses.title | 23502 | column title; no named constraint | 422 for invalid input; 500 if validation incorrectly allowed it |
| 2 | courses.credits = 0 | 23514 | courses_credits_check | 422 |
| 3 | courses.likes = -1 | 23514 | courses_likes_check | 500, because only server code changes the counter |
| 4 | One-character student name | 23514 | students_name_check | 422 |
| 5 | Duplicate student email | 23505 | students_email_key | 409 Conflict |
| 6 | Duplicate course ID | 23505 | courses_pkey | 409 Conflict |
| 7 | Repeated enrollment | 23505 | enrollments_course_id_student_id_key | 409 Conflict |
| 8 | Enrollment in missing course | 23503 | enrollments_course_id_fkey | 404 Course not found |
| 9 | Enrollment of missing student | 23503 | enrollments_student_id_fkey | 404 Student not found |
| 10 | Delete an enrolled course | 23001 | enrollments_course_id_fkey | 409 Conflict |
| 11 | Delete Daniyar, then roll back | No error | enrollments_student_id_fkey, CASCADE | Successful deletion: enrollments 6 → 3 → 6 after ROLLBACK |

PostgreSQL 16–17 use `23503` for the restricted deletion; PostgreSQL 18 reports `23001`. Messages also vary by version and language. Both missing parent rows and restricted deletion can involve the same foreign key, so the operation context matters when choosing the HTTP response.

All ten rejected statements left the data at 6/3/6. The cascade removed exactly Daniyar's three enrollments, and rollback restored both the student and enrollments. Failed inserts and rolled-back inserts consume identity values; gaps do not violate uniqueness.

Pydantic gives API clients early, readable validation errors. A database CHECK also protects writes from SQL clients, scripts, migrations and other applications that bypass the API, and catches regressions in application validation. Both layers are needed to preserve the invariant.

## Index: EXPLAIN before and after

The disposable `idx_demo` held 500 courses, 20,000 students and 50,000 enrollments from `experiments/idx_data.sql`. The benchmark dropped only `enrollments_student_id_idx` before the first measurement, then recreated it. Query: `SELECT * FROM enrollments WHERE student_id = 777;`.

| Metric | Before index | After index |
|---|---|---|
| Access method | Seq Scan | Bitmap Heap Scan with Bitmap Index Scan |
| Estimated cost | 0.00..1042.00 | 4.31..15.59 |
| Rows Removed by Filter | 49997 | 0 |
| Smallest Execution Time of three runs | 2.167 ms | 0.005 ms |

Actual representative plans (the table above uses the minimum of three separately recorded runs):

```text
Seq Scan on enrollments  (cost=0.00..1042.00 rows=3 width=34) (actual time=0.038..2.190 rows=3.00 loops=1)
  Filter: (student_id = 777)
  Rows Removed by Filter: 49997
  Buffers: shared hit=417
Planning Time: 0.013 ms
Execution Time: 2.191 ms
```

```text
Bitmap Heap Scan on enrollments  (cost=4.31..15.59 rows=3 width=34) (actual time=0.002..0.003 rows=3.00 loops=1)
  Recheck Cond: (student_id = 777)
  Heap Blocks: exact=3
  Buffers: shared hit=5
  ->  Bitmap Index Scan on enrollments_student_id_idx  (cost=0.00..4.31 rows=3 width=0) (actual time=0.001..0.001 rows=3.00 loops=1)
        Index Cond: (student_id = 777)
        Index Searches: 1
        Buffers: shared hit=2
Planning Time: 0.007 ms
Execution Time: 0.004 ms
```

The table occupied 3336 kB and the index 896 kB. Times depend on cache and hardware; the change in access method is the durable observation. [Raw measurements](verification/experiments.json) include all six JSON plans, both text plans, buffer usage, index sizes, and the email/course lookup plans.

1. Primary keys and UNIQUE constraints create indexes automatically; a referencing foreign key does not. The `(course_id, student_id)` unique index supports searches starting with `course_id`, while a selective lookup on only `student_id` needed its own index in this experiment.
2. A primary-key lookup in the six-row courses table used Seq Scan because one sequential page was cheaper than visiting an index and then a heap page. An index is an available access path; PostgreSQL chooses it only when its estimated cost is favorable.
3. The student index speeds up listing one student's enrollments and finding their child rows during a cascading deletion. It consumes space and adds work to writes, so indexes should serve actual queries.

To reproduce the benchmark manually, load schema and `experiments/idx_data.sql` into **idx_demo**, drop the student index, `ANALYZE`, and run EXPLAIN ANALYZE three times. Recreate the index and repeat. The shipped schema always contains the final index.

## Transaction

The experiment uses two independent PostgreSQL connections, corresponding to windows A and B:

- A inserted Madina and then attempted an enrollment in a missing course. The second insert failed with `23503`; subsequent SELECT failed with `25P02` because the transaction was aborted. After ROLLBACK, Madina's count was zero: the successful first insert was undone too.
- In the successful variant, A inserted Madina and her web-security enrollment in one transaction. B saw **0 students and 0 enrollments** for Madina before COMMIT, then **1 and 1** after COMMIT. The default isolation level was `read committed`; the complete operation became visible together.
- Without a transaction, a committed first insert would survive failure of the second and leave a student without the intended enrollment. Keep one API operation in one short transaction and close it promptly to release its locks.

The final reset restored 6/3/6. [Transaction observations and row-lock check](verification/experiments.json) were recorded from the actual connections.

## Self-review against the checklist

| What to check | Result |
|---|---|
| Keys | Yes: every table has a primary key; both enrollment references have foreign keys. |
| Types | Yes: text slugs, bigint identity keys, integer counts, boolean flags and timestamptz instants. |
| Required values | Yes: all domain columns are NOT NULL; no required fact can silently be absent. |
| Constraints | Yes: positive credits, nonnegative likes, name length, unique email and unique course/student pair; name length agrees with Pydantic. |
| Deletion | Yes: course RESTRICT and student CASCADE are intentional and were tested. |
| Normalization | Yes: course and student facts occur once; enrollments contain references and their own timestamp. |
| Indexes and names | Yes: the pair index covers course_id, a separate index covers student_id; all names use snake_case and match the ORM in Lab 7. |

## Verification and bonus experiments

[Clean-start output](verification/clean-start.log) records schema, seed, and **two consecutive executions** of queries.sql with `ON_ERROR_STOP=1`; both executions succeeded without changing the seeded facts. The first page has likes 24/21/19, the second page contains databases-postgresql with 15. Query 6 returns enrollment counts 3/2/1/0/0/0.

Optional work completed:

- **Bonus 1:** [norm_demo.sql](experiments/norm_demo.sql) and [actual output](verification/normalization.log) show all three flat-table anomalies. Updating one registration gave one course two titles; deleting the last FastAPI registration lost the course; inserting a course without registrations required NULL student fields. Normalization stored 3 courses, 3 students and 6 registrations. Only three courses could be recovered because the flat table never stored the courses without registrations.
- **Bonus 2:** both clients read 11 and wrote 12, losing a like. Atomic increments produced 13. With A's transaction open, `pg_blocking_pids` confirmed B waited for A's row lock; after A committed, B incremented the fresh value to 13. The initial counter was restored.
- **Bonus 3:** the concatenated condition `id='x' OR '1'='1'` returned all six courses. Passing the entire attack string as a bound parameter returned zero rows: input was a value rather than SQL syntax.
- **Bonus 4:** queries 7 and 8 are included: the empty courses are api-design, databases-postgresql and web-security; Daniyar has 3 courses and Aigerim 2. HAVING filters aggregated groups after WHERE filters input rows.

For an automated replay, create disposable `lab6_verify` and `idx_demo` databases owned by catalog_app, and use the backend environment (psycopg 3):

```bash
LAB6_DSN='postgresql://catalog_app:change-me@localhost:5432/lab6_verify' \
LAB6_INDEX_DSN='postgresql://catalog_app:change-me@localhost:5432/idx_demo' \
../04-backend/.venv/bin/python experiments/verify.py
```

The script refuses other database names and resets only the explicitly supplied disposable databases. In a standalone checkout, replace `../04-backend/.venv/bin/python` with a Python environment containing psycopg 3 (`python -m pip install 'psycopg[binary]'`). The core SQL project needs only psql; Python is an optional experiment runner. There are at least six separate commits for this directory in the workspace history.
