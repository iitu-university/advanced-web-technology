"""Check GraphQL permissions, nullable email and HTTP authentication failures."""

import httpx

from lab9_checks import ADMIN, BASE, STUDENT, authorization, finish

ME = "{ me { email role } }"
STUDENTS = "{ students { id } }"
OTHER = '{ student(id: "2") { name email } }'
OWN = '{ student(id: "1") { email } }'
NESTED = "{ enrollments(limit: 4) { student { email } } }"


def error_at(body: dict, path: list, message: str) -> bool:
    return any(
        error.get("path") == path and error.get("message") == message
        for error in body.get("errors", [])
    )


with httpx.Client(base_url=BASE) as client:
    student = authorization(client, STUDENT)
    admin = authorization(client, ADMIN)

    def ask(query: str, headers: dict | None = None) -> dict:
        response = client.post("/graphql", json={"query": query}, headers=headers)
        assert response.status_code == 200, response.status_code
        return response.json()

    partial = ask(OTHER, student)
    nested = ask(NESTED, student)
    emails = [row["student"]["email"] for row in nested["data"]["enrollments"]]
    hidden_paths = [["enrollments", index, "student", "email"] for index, email in enumerate(emails) if email is None]
    bad_token = client.post("/graphql", json={"query": ME}, headers={"Authorization": "Bearer invalid"})
    checks = {
        "anonymous me": error_at(ask(ME), ["me"], "Authentication required"),
        "student me": ask(ME, student) == {"data": {"me": {"email": STUDENT[0], "role": "student"}}},
        "student listing denied": error_at(ask(STUDENTS, student), ["students"], "Admin role required"),
        "admin listing": ask(STUDENTS, admin) == {"data": {"students": [{"id": "1"}, {"id": "2"}, {"id": "3"}]}},
        "other profile keeps name, hides email": (
            partial.get("data") == {"student": {"name": "Daniyar Bekov", "email": None}}
            and error_at(partial, ["student", "email"], "Not allowed to read this field")
        ),
        "own email": ask(OWN, student) == {"data": {"student": {"email": STUDENT[0]}}},
        "admin reads other email": ask(OTHER, admin) == {
            "data": {"student": {"name": "Daniyar Bekov", "email": "daniyar@example.com"}}
        },
        "nested email uses same permission": (
            emails.count(STUDENT[0]) == 2 and len(hidden_paths) == 2
            and all(error_at(nested, path, "Not allowed to read this field") for path in hidden_paths)
        ),
        "invalid bearer rejected before GraphQL": (
            bad_token.status_code == 401 and bad_token.headers.get("www-authenticate") == "Bearer"
            and bad_token.headers["content-type"].startswith("application/problem+json")
        ),
    }

for label, passed in checks.items():
    print(f"{'ok  ' if passed else 'FAIL'} {label}")
finish(list(checks.values()))
