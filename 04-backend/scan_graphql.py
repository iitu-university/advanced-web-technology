"""Review anonymous read permissions and inspect mutation permissions in the schema."""

import httpx

from graphql_api import schema
from lab9_checks import BASE

READS = {
    "Query.courses": "{ courses(limit: 1) { id } }",
    "Query.course": '{ course(id: "api-design") { id } }',
    "Query.me": "{ me { id } }",
    "Query.students": "{ students(limit: 1) { id } }",
    "Query.student": '{ student(id: "1") { id } }',
    "Query.enrollments": "{ enrollments(limit: 1) { id } }",
    "Course.enrollments": "{ courses(limit: 1) { enrollments { id } } }",
    "Student.enrollments": '{ student(id: "1") { enrollments { id } } }',
    "Student.email": '{ student(id: "1") { email } }',
}

print(f"{'field':<24}anonymous")
with httpx.Client(base_url=BASE) as client:
    for field, query in READS.items():
        response = client.post("/graphql", json={"query": query})
        response.raise_for_status()
        errors = response.json().get("errors", [])
        print(f"{field:<24}{errors[0]['message'] if errors else 'open'}")

for name in ("enroll", "likeCourse"):
    field = schema.get_field_for_type(name, "Mutation")
    if field is None:
        raise RuntimeError(f"Mutation.{name} is missing from the schema")
    guard = ", ".join(permission.__name__ for permission in field.permission_classes)
    print(f"{f'Mutation.{name}':<24}{guard or 'no declared permission'} (schema)")
