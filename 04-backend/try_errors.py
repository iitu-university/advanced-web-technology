"""Check REST rule errors and their RFC 9457 representations."""

import httpx

BASE = "http://localhost:8000"
CASES = [
    ("email already taken", "/students", {"name": "Aigerim Two", "email": "aigerim@example.com"}, 409, "email-taken"),
    ("already enrolled", "/enrollments", {"courseId": "ai-integration", "studentId": 3}, 409, "already-enrolled"),
    ("unknown course", "/enrollments", {"courseId": "nope", "studentId": 3}, 404, "course-not-found"),
    ("unknown student", "/enrollments", {"courseId": "web-security", "studentId": 999}, 404, "student-not-found"),
    ("name too short", "/students", {"name": "N", "email": "n@example.com"}, 422, None),
]

failed = 0
for title, path, body, status, slug in CASES:
    response = httpx.post(BASE + path, json=body)
    actual_slug = response.json().get("type", "").rsplit("/", 1)[-1]
    expected_type = "application/problem+json" if slug else "application/json"
    ok = response.status_code == status and response.headers["content-type"].startswith(expected_type) and (actual_slug == slug if slug else "detail" in response.json())
    failed += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {title:<21} {response.status_code}  {response.headers.get('content-type')}  {actual_slug or '-'}")
print(f"{len(CASES) - failed} of {len(CASES)} as expected")
if failed:
    raise SystemExit(1)
