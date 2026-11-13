"""Read-only GraphQL checks and expected mutation errors."""

import httpx

URL = "http://localhost:8000/graphql"


def enroll(course_id: str, student_id: str) -> str:
    return ("mutation { enroll(input: "
            f'{{courseId: "{course_id}", studentId: "{student_id}"}}) '
            "{ enrollment { id } userErrors { code } } }")


def first_error(data):
    return data["errors"][0]["message"].split(". Did you")[0]


CASES = [
    ("courses(limit: 2)", "{ courses(limit: 2) { id } }", lambda d: ",".join(c["id"] for c in d["data"]["courses"]), "ai-integration,modern-frontend"),
    ('course(id: "api-design")', '{ course(id: "api-design") { title } }', lambda d: d["data"]["course"]["title"], "API Design: REST vs GraphQL"),
    ('course(id: "nope")', '{ course(id: "nope") { title } }', lambda d: str(d["data"]["course"]), "None"),
    ("student(id: 2) → courses", "{ student(id: 2) { enrollments { course { id } } } }", lambda d: str(len(d["data"]["student"]["enrollments"])), "3"),
    ("enroll twice", enroll("ai-integration", "3"), lambda d: d["data"]["enroll"]["userErrors"][0]["code"], "ALREADY_ENROLLED"),
    ("enroll: unknown course", enroll("nope", "3"), lambda d: d["data"]["enroll"]["userErrors"][0]["code"], "COURSE_NOT_FOUND"),
    ("enroll: unknown student", enroll("web-security", "999"), lambda d: d["data"]["enroll"]["userErrors"][0]["code"], "STUDENT_NOT_FOUND"),
    ("unknown field", '{ course(id: "api-design") { titel } }', first_error, "Cannot query field 'titel' on type 'Course'"),
]

failed = 0
for title, query, pick, expected in CASES:
    body = httpx.post(URL, json={"query": query}).json()
    try:
        actual = pick(body)
    except (KeyError, IndexError, TypeError):
        actual = "?"
    ok = actual == expected
    failed += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {title:<28} {actual}")
print(f"{len(CASES) - failed} of {len(CASES)} as expected")
if failed:
    raise SystemExit(1)
