"""Run the Lab 6 experiments in disposable databases, using real PostgreSQL.

Requires psycopg 3 (available in ../04-backend/.venv). The explicitly supplied
databases are reset. Use lab6_verify and idx_demo, never a database with real data.
"""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ("NULL title", "INSERT INTO courses (id,title,description,credits) VALUES ('x-test',NULL,'Test',3)", "23502", None, 422),
    ("zero credits", "INSERT INTO courses (id,title,description,credits) VALUES ('x-test','Test','Test',0)", "23514", "courses_credits_check", 422),
    ("negative likes", "UPDATE courses SET likes=-1 WHERE id='api-design'", "23514", "courses_likes_check", 500),
    ("short name", "INSERT INTO students (name,email) VALUES ('A','a@example.com')", "23514", "students_name_check", 422),
    ("duplicate email", "INSERT INTO students (name,email) VALUES ('Dup Student','aigerim@example.com')", "23505", "students_email_key", 409),
    ("duplicate course", "INSERT INTO courses (id,title,description,credits) VALUES ('api-design','x','y',1)", "23505", "courses_pkey", 409),
    ("duplicate enrollment", "INSERT INTO enrollments (course_id,student_id) VALUES ('modern-frontend',1)", "23505", "enrollments_course_id_student_id_key", 409),
    ("unknown course", "INSERT INTO enrollments (course_id,student_id) VALUES ('no-such-course',1)", "23503", "enrollments_course_id_fkey", 404),
    ("unknown student", "INSERT INTO enrollments (course_id,student_id) VALUES ('web-security',999)", "23503", "enrollments_student_id_fkey", 404),
    ("restricted delete", "DELETE FROM courses WHERE id='modern-frontend'", None, "enrollments_course_id_fkey", 409),
]


def counts(conn):
    return list(conn.execute("SELECT (SELECT count(*) FROM courses), (SELECT count(*) FROM students), (SELECT count(*) FROM enrollments)").fetchone())


def reset(conn):
    conn.execute((ROOT / "schema.sql").read_text())
    conn.execute((ROOT / "seed.sql").read_text())


def main():
    report = {"checked_at": datetime.now(timezone.utc).isoformat()}
    with psycopg.connect(os.environ["LAB6_DSN"], autocommit=True) as conn:
        assert conn.info.dbname == "lab6_verify", "Use a disposable database named lab6_verify"
        reset(conn)
        report["server_version"] = conn.execute("SHOW server_version").fetchone()[0]
        report["initial_counts"] = counts(conn)
        assert report["initial_counts"] == [6, 3, 6]
        report["violations"] = []
        for title, sql, code, constraint, http_status in CASES:
            try:
                conn.execute(sql)
            except psycopg.IntegrityError as exc:
                assert exc.sqlstate == code if code else exc.sqlstate in {"23001", "23503"}
                if constraint:
                    assert exc.diag.constraint_name == constraint
                report["violations"].append({"case": title, "sqlstate": exc.sqlstate, "constraint": exc.diag.constraint_name, "column": exc.diag.column_name, "http": http_status, "message": str(exc)})
            else:
                raise AssertionError(f"Constraint did not fire: {title}")
        conn.execute("BEGIN")
        conn.execute("DELETE FROM students WHERE email='daniyar@example.com'")
        report["cascade_during"] = counts(conn)
        conn.execute("ROLLBACK")
        report["cascade_after_rollback"] = counts(conn)
        assert report["cascade_during"] == [6, 2, 3]
        assert counts(conn) == [6, 3, 6]

        conn.execute("BEGIN")
        conn.execute("INSERT INTO students (name,email) VALUES ('Madina Ospanova','madina@example.com')")
        try:
            conn.execute("INSERT INTO enrollments (course_id,student_id) SELECT 'no-such-course',id FROM students WHERE email='madina@example.com'")
        except psycopg.IntegrityError as exc:
            report["transaction_insert_error"] = exc.sqlstate
        try:
            conn.execute("SELECT count(*) FROM students")
        except psycopg.errors.InFailedSqlTransaction as exc:
            report["aborted_transaction_error"] = exc.sqlstate
        conn.execute("ROLLBACK")
        assert conn.execute("SELECT count(*) FROM students WHERE email='madina@example.com'").fetchone()[0] == 0

        with psycopg.connect(os.environ["LAB6_DSN"], autocommit=True) as observer:
            conn.execute("BEGIN")
            conn.execute("INSERT INTO students (name,email) VALUES ('Madina Ospanova','madina@example.com')")
            conn.execute("INSERT INTO enrollments (course_id,student_id) SELECT 'web-security',id FROM students WHERE email='madina@example.com'")
            visibility_sql = "SELECT (SELECT count(*) FROM students WHERE email='madina@example.com'), (SELECT count(*) FROM enrollments e JOIN students s ON s.id=e.student_id WHERE s.email='madina@example.com')"
            report["observer_before_commit"] = list(observer.execute(visibility_sql).fetchone())
            conn.execute("COMMIT")
            report["observer_after_commit"] = list(observer.execute(visibility_sql).fetchone())
            assert report["observer_before_commit"] == [0, 0]
            assert report["observer_after_commit"] == [1, 1]
            report["isolation"] = observer.execute("SHOW default_transaction_isolation").fetchone()[0]
            a = conn.execute("SELECT likes FROM courses WHERE id='api-design'").fetchone()[0]
            b = observer.execute("SELECT likes FROM courses WHERE id='api-design'").fetchone()[0]
            conn.execute("UPDATE courses SET likes=%s WHERE id='api-design'", (a + 1,))
            observer.execute("UPDATE courses SET likes=%s WHERE id='api-design'", (b + 1,))
            report["lost_update"] = conn.execute("SELECT likes FROM courses WHERE id='api-design'").fetchone()[0]
            conn.execute("UPDATE courses SET likes=11 WHERE id='api-design'")
            conn.execute("BEGIN")
            conn.execute("UPDATE courses SET likes=likes+1 WHERE id='api-design'")
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(lambda: observer.execute("UPDATE courses SET likes=likes+1 WHERE id='api-design' RETURNING likes").fetchone()[0])
                try:
                    for _ in range(100):
                        blockers = conn.execute("SELECT pg_blocking_pids(%s)", (observer.info.backend_pid,)).fetchone()[0]
                        if blockers:
                            break
                        time.sleep(0.01)
                    assert conn.info.backend_pid in blockers
                    report["row_lock_observed"] = True
                finally:
                    conn.execute("COMMIT")
                report["atomic_update"] = future.result(timeout=5)
            assert report["lost_update"] == 12 and report["atomic_update"] == 13

        reset(conn)
        report["unsafe_injection_rows"] = len(conn.execute("SELECT id FROM courses WHERE id='x' OR '1'='1'").fetchall())
        report["parameterized_injection_rows"] = len(conn.execute("SELECT id FROM courses WHERE id=%s", ("x' OR '1'='1",)).fetchall())
        assert report["unsafe_injection_rows"] == 6 and report["parameterized_injection_rows"] == 0
        conn.execute("ANALYZE courses")
        report["small_table_plan"] = [r[0] for r in conn.execute("EXPLAIN SELECT * FROM courses WHERE id='api-design'")]
        report["final_counts"] = counts(conn)

    with psycopg.connect(os.environ["LAB6_INDEX_DSN"], autocommit=True) as conn:
        assert conn.info.dbname == "idx_demo", "Use a disposable database named idx_demo"
        conn.execute((ROOT / "schema.sql").read_text())
        conn.execute("DROP INDEX enrollments_student_id_idx")
        conn.execute((ROOT / "experiments/idx_data.sql").read_text())
        report["index_counts"] = counts(conn)
        assert report["index_counts"] == [500, 20000, 50000]
        for label, sql in [("email_plan", "SELECT * FROM students WHERE email='student777@example.com'"), ("course_plan", "SELECT * FROM enrollments WHERE course_id='course-7'")]:
            report[label] = [r[0] for r in conn.execute("EXPLAIN " + sql)]
        for phase in ("before", "after"):
            if phase == "after":
                conn.execute("CREATE INDEX enrollments_student_id_idx ON enrollments (student_id)")
            report[phase] = [conn.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT * FROM enrollments WHERE student_id=777").fetchone()[0][0] for _ in range(3)]
            report[phase + "_plan"] = [r[0] for r in conn.execute("EXPLAIN ANALYZE SELECT * FROM enrollments WHERE student_id=777")]
        report["sizes"] = list(conn.execute("SELECT pg_size_pretty(pg_relation_size('enrollments')), pg_size_pretty(pg_relation_size('enrollments_student_id_idx'))").fetchone())
    output = ROOT / "verification"
    output.mkdir(exist_ok=True)
    (output / "experiments.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
