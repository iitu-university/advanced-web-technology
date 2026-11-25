"""Check the REST role matrix using the teaching data and one unused course."""

import httpx
from sqlalchemy import delete, select

from db import SessionLocal
from lab9_checks import ADMIN, BASE, STUDENT, authorization, finish
from models import Enrollment

COURSE = "web-security"
ROWS = (
    ("GET /courses", "GET", "/courses", None, (200, 200, 200)),
    ("GET /me", "GET", "/me", None, (401, 200, 200)),
    ("GET /enrollments", "GET", "/enrollments", None, (401, 403, 200)),
    ("POST /enrollments (self)", "POST", "/enrollments", 1, (401, 201, None)),
    ("POST /enrollments (another)", "POST", "/enrollments", 2, (401, 403, 201)),
)

with SessionLocal() as db:
    if db.scalar(select(Enrollment.id).where(Enrollment.course_id == COURSE).limit(1)):
        raise SystemExit(f"Use the seeded database with no enrollments in {COURSE}.")

checks = []
with httpx.Client(base_url=BASE) as client:
    roles = {"anonymous": {}, "student": authorization(client, STUDENT), "admin": authorization(client, ADMIN)}
    print(f"{'request':<32}" + "".join(f"{role:<14}" for role in roles))
    for title, method, path, student_id, expected in ROWS:
        cells = []
        for headers, status in zip(roles.values(), expected):
            if status is None:
                cells.append("-")
                continue
            body = {"courseId": COURSE, "studentId": student_id} if student_id is not None else None
            response = client.request(method, path, headers=headers, json=body)
            got = response.status_code
            if method == "POST" and got == 201:
                with SessionLocal.begin() as db:
                    db.execute(delete(Enrollment).where(Enrollment.id == response.json()["id"]))
            challenge = response.headers.get("www-authenticate")
            passed = got == status and challenge == ("Bearer" if status == 401 else None)
            if status in {401, 403}:
                passed &= response.headers["content-type"].startswith("application/problem+json")
            checks.append(passed)
            cells.append(str(got) if passed else f"{got} FAIL")
        print(f"{title:<32}" + "".join(f"{cell:<14}" for cell in cells))
finish(checks)
