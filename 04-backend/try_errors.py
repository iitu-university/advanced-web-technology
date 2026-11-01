"""Check the five required error responses against a running, seeded API."""
import os

import httpx


BASE = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
CASES = [
    ("email already taken", "/students", {"name": "Aigerim Two", "email": "aigerim@example.com"}, 409),
    ("already enrolled", "/enrollments", {"courseId": "ai-integration", "studentId": 3}, 409),
    ("unknown course", "/enrollments", {"courseId": "nope", "studentId": 3}, 404),
    ("unknown student", "/enrollments", {"courseId": "web-security", "studentId": 999}, 404),
    ("name too short", "/students", {"name": "N", "email": "n@example.com"}, 422),
]


def main() -> None:
    failed = 0
    with httpx.Client(base_url=BASE, timeout=10) as client:
        for title, path, body, expected in CASES:
            response = client.post(path, json=body)
            ok = response.status_code == expected
            failed += not ok
            print(f"{'ok  ' if ok else 'FAIL'} {title:<20} {response.status_code}  {response.text[:100]}")
    print(f"{len(CASES) - failed} of {len(CASES)} as expected")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
