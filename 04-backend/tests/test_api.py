"""Real PostgreSQL tests. TEST_DATABASE_URL must name a disposable *_test database."""
import importlib.util
import os
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

TEST_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_URL or not make_url(TEST_URL).database.endswith("_test"):
    raise RuntimeError("Set TEST_DATABASE_URL to a disposable PostgreSQL database ending in _test")
os.environ["DATABASE_URL"] = TEST_URL

from fastapi.testclient import TestClient

from db import SessionLocal, engine
from main import CONSTRAINT_ERRORS, app, raise_http_error
from models import Course, Enrollment, Student
from schemas import EnrollmentIn, StudentIn

ROOT = Path(__file__).resolve().parents[1]
SEED = (ROOT / "seed.sql").read_text()


def alembic(*args):
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args], cwd=ROOT,
        capture_output=True, text=True, env={**os.environ, "DATABASE_URL": TEST_URL},
    )
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout + result.stderr


def seed():
    with engine.connect() as conn:
        conn.exec_driver_sql(SEED)
        conn.commit()


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        alembic("upgrade", "head")

    def setUp(self):
        seed()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_openapi_docs_and_camel_case(self):
        schema = self.client.get("/openapi.json").json()
        self.assertEqual(sum(len(methods) for methods in schema["paths"].values()), 8)
        self.assertEqual(self.client.get("/docs").status_code, 200)
        fields = schema["components"]["schemas"]["CourseOut"]["properties"]
        self.assertIn("isElective", fields)
        self.assertIn("level", fields)
        self.assertNotIn("is_elective", fields)
        self.assertEqual(self.client.get("/").json(), {"message": "Course Catalog API is running"})

    def test_catalog_filters_order_search_and_pagination(self):
        courses = self.client.get("/courses").json()
        self.assertEqual(len(courses), 6)
        self.assertEqual(courses[0]["id"], "ai-integration")
        self.assertEqual(courses[-1]["id"], "api-design")
        self.assertEqual(set(courses[0]), {"id", "title", "description", "credits", "isElective", "likes", "level"})
        self.assertEqual([c["id"] for c in self.client.get("/courses?is_elective=true").json()], ["ai-integration", "api-design"])
        self.assertEqual(len(self.client.get("/courses?isElective=true").json()), 6)
        self.assertEqual(len(self.client.get("/courses?is_elective=false").json()), 4)
        self.assertEqual(len(self.client.get("/courses?level=beginner").json()), 2)
        self.assertEqual(self.client.get("/courses?level=beginner&is_elective=false").json(), [])
        self.assertEqual(self.client.get("/courses?is_elective=false&page_size=3&page=2").json()[0]["id"], "databases-postgresql")
        titles = [c["title"] for c in self.client.get("/courses?sort=title").json()]
        self.assertEqual(titles, sorted(titles))
        self.assertEqual(self.client.get("/courses?q=FASTAPI").json()[0]["id"], "backend-fastapi")
        self.assertEqual(self.client.get("/courses", params={"q": "%"}).json(), [])
        self.assertEqual(self.client.get("/courses", params={"q": "_"}).json(), [])
        self.assertEqual(self.client.get("/courses", params={"q": "x' OR '1'='1"}).json(), [])
        for query in ("page=0", "page_size=0", "page_size=101", "sort=nope"):
            self.assertEqual(self.client.get("/courses?" + query).status_code, 422)

    def test_tied_likes_have_stable_pages(self):
        with engine.begin() as conn:
            conn.execute(text("UPDATE courses SET likes=10"))
        first = self.client.get("/courses?page_size=3").json()
        second = self.client.get("/courses?page_size=3&page=2").json()
        ids = [c["id"] for c in first + second]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(set(ids)), 6)

    def test_like_is_committed_and_survives_a_new_engine(self):
        response = self.client.post("/courses/web-security/like")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["likes"], 22)
        restarted_engine = create_engine(TEST_URL)
        try:
            with restarted_engine.connect() as conn:
                self.assertEqual(conn.execute(text("SELECT likes FROM courses WHERE id='web-security'")).scalar_one(), 22)
        finally:
            restarted_engine.dispose()

    def test_concurrent_likes_do_not_lose_updates(self):
        def like(_):
            with TestClient(app) as client:
                return client.post("/courses/api-design/like").status_code
        with ThreadPoolExecutor(max_workers=6) as pool:
            self.assertEqual(list(pool.map(like, range(12))), [200] * 12)
        self.assertEqual(self.client.get("/courses/api-design").json()["likes"], 23)

    def test_missing_course_is_404(self):
        for method, path in [(self.client.get, "/courses/nope"), (self.client.post, "/courses/nope/like")]:
            response = method(path)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"detail": "Course not found"})

    def test_create_student_and_enroll_with_server_timestamp(self):
        response = self.client.post("/students", json={"name": "Nurlan Abenov", "email": "nurlan@example.com"})
        self.assertEqual(response.status_code, 201)
        student_id = response.json()["id"]
        self.assertEqual(student_id, 4)
        enrolled = self.client.post("/enrollments", json={"courseId": "web-security", "studentId": student_id})
        self.assertEqual(enrolled.status_code, 201)
        body = enrolled.json()
        self.assertEqual(set(body), {"id", "courseId", "studentId", "enrolledAt"})
        self.assertIsNotNone(datetime.fromisoformat(body["enrolledAt"]).tzinfo)
        self.assertEqual(body["studentId"], student_id)
        rows = self.client.get("/enrollments").json()
        self.assertEqual(rows[-1]["studentName"], "Nurlan Abenov")
        self.assertEqual(rows[-1]["courseTitle"], "Web Security Essentials")

    def test_five_required_error_cases_and_session_recovery(self):
        from try_errors import CASES
        for title, path, body, expected in CASES:
            with self.subTest(title):
                response = self.client.post(path, json=body)
                self.assertEqual(response.status_code, expected)
        self.assertEqual(len(self.client.get("/enrollments").json()), 6)
        created = self.client.post("/students", json={"name": "Valid User", "email": "valid@example.com"})
        self.assertEqual(created.status_code, 201)
        self.assertGreater(created.json()["id"], 4)  # Failed inserts consume identities.

    def test_validation_and_retired_student_name_contract(self):
        for body in [{"name": "A", "email": "a@example.com"}, {"name": "Dana", "email": "invalid"}]:
            self.assertEqual(self.client.post("/students", json=body).status_code, 422)
        old = self.client.post("/enrollments", json={"courseId": "web-security", "studentName": "Dana"})
        self.assertEqual(old.status_code, 422)
        self.assertEqual(old.json()["detail"][0]["loc"], ["body", "studentId"])
        self.assertEqual(EnrollmentIn(course_id="api-design", student_id=1).student_id, 1)
        self.assertEqual(StudentIn(name="Dana", email="dana@example.com").name, "Dana")

    def test_concurrent_duplicate_enrollment_is_a_conflict(self):
        def enroll(_):
            with TestClient(app) as client:
                return client.post("/enrollments", json={"courseId": "web-security", "studentId": 3}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(enroll, range(2))), [201, 409])

    def test_join_statistics_keep_zero_counts(self):
        stats = self.client.get("/stats/courses").json()
        self.assertEqual(stats, [
            {"courseId": "ai-integration", "enrolled": 3},
            {"courseId": "modern-frontend", "enrolled": 2},
            {"courseId": "backend-fastapi", "enrolled": 1},
            {"courseId": "api-design", "enrolled": 0},
            {"courseId": "databases-postgresql", "enrolled": 0},
            {"courseId": "web-security", "enrolled": 0},
        ])
        self.assertEqual(sum(row["enrolled"] for row in stats), len(self.client.get("/enrollments").json()))

    def test_unknown_integrity_error_is_not_disguised_as_user_error(self):
        with SessionLocal() as db:
            db.add(Student(name="N", email="short@example.com"))
            with self.assertRaises(IntegrityError) as rejected:
                db.commit()
            with self.assertRaises(IntegrityError):
                raise_http_error(rejected.exception)
        with patch.dict(CONSTRAINT_ERRORS, {}, clear=True), TestClient(app, raise_server_exceptions=False) as client:
            response = client.post("/students", json={"name": "Duplicate", "email": "aigerim@example.com"})
            self.assertEqual(response.status_code, 500)

    def test_database_deletion_rules(self):
        with SessionLocal() as db:
            db.delete(db.get(Course, "modern-frontend"))
            with self.assertRaises(IntegrityError):
                db.commit()
        with SessionLocal() as db:
            db.delete(db.get(Student, 2))
            db.commit()
        self.assertEqual(len(self.client.get("/enrollments").json()), 3)

    def test_cors_origins_and_json_preflight(self):
        allowed = self.client.get("/", headers={"Origin": "http://localhost:3000"})
        self.assertEqual(allowed.headers["access-control-allow-origin"], "http://localhost:3000")
        self.assertEqual(allowed.headers["vary"], "Origin")
        self.assertNotIn("access-control-allow-origin", self.client.get("/", headers={"Origin": "http://evil.example"}).headers)
        headers = {"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}
        response = self.client.options("/enrollments", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("POST", response.headers["access-control-allow-methods"])
        self.assertEqual(response.headers["access-control-max-age"], "600")
        self.assertEqual(self.client.options("/enrollments", headers={**headers, "Origin": "http://localhost:3000/"}).status_code, 400)

    def test_bonus_configurable_origins(self):
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:3000,http://127.0.0.1:3000"}):
            spec = importlib.util.spec_from_file_location("bonus_app", ROOT / "main.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            with TestClient(module.app) as client:
                for origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
                    self.assertEqual(client.get("/", headers={"Origin": origin}).headers["access-control-allow-origin"], origin)

    def test_migration_round_trip_with_existing_data(self):
        before = self.client.get("/courses").json()
        self.assertIn("No new upgrade operations", alembic("check"))
        alembic("downgrade", "-1")
        self.assertNotIn("level", {c["name"] for c in inspect(engine).get_columns("courses")})
        alembic("upgrade", "head")
        self.assertEqual(self.client.get("/courses").json(), before)
        self.assertIn("0002 (head)", alembic("current"))
        self.assertEqual(alembic("heads").strip(), "0002 (head)")
        self.assertIn("No new upgrade operations", alembic("check"))

    def test_migrations_can_recreate_the_entire_schema(self):
        alembic("downgrade", "base")
        self.assertEqual(inspect(engine).get_table_names(), ["alembic_version"])
        alembic("upgrade", "head")
        seed()
        self.assertEqual(len(self.client.get("/courses").json()), 6)
        self.assertIn("No new upgrade operations", alembic("check"))


if __name__ == "__main__":
    unittest.main()
