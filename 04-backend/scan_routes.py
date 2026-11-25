"""Audit the local catalog's OpenAPI routes without submitting valid writes."""

import re

import httpx

from lab9_checks import ADMIN, BASE, STUDENT, authorization

SKIP = {"/auth/login", "/graphql"}
KNOWN_WRITES = {"/courses/{course_id}/like", "/students", "/enrollments"}

with httpx.Client(base_url=BASE) as client:
    roles = {"anonymous": {}, "student": authorization(client, STUDENT), "admin": authorization(client, ADMIN)}
    description = client.get("/openapi.json")
    description.raise_for_status()
    open_routes = []
    print(f"{'route':<44}" + "".join(f"{role:<12}" for role in roles))
    for path, operations in description.json()["paths"].items():
        if path in SKIP:
            continue
        for method in operations:
            if method != "get" and not (method == "post" and path in KNOWN_WRITES):
                continue
            probe = re.sub(r"\{[^}]+\}", "0", path)
            name = f"{method.upper()} {path}"
            codes = [
                client.request(method.upper(), probe, headers=headers, json={} if method == "post" else None).status_code
                for headers in roles.values()
            ]
            print(f"{name:<44}" + "".join(f"{code:<12}" for code in codes))
            if codes[0] in {200, 404, 422}:
                open_routes.append(name)

print(f"\nopen without a token ({len(open_routes)}):")
for route in open_routes:
    print(f"  {route}")
