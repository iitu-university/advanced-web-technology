"""Check credential handling and the /me response against the local API."""

import httpx

from lab9_checks import BASE, STUDENT, finish, login

with httpx.Client(base_url=BASE) as client:
    good = login(client, *STUDENT)
    token = good.json().get("access_token", "")
    cases = [
        ("correct password", good, 200, "bearer"),
        ("wrong password", login(client, STUDENT[0], "wrong-password"), 401, "Incorrect email or password"),
        ("unknown email", login(client, "nobody@example.com", "wrong-password"), 401, "Incorrect email or password"),
        ("/me without token", client.get("/me"), 401, "Not authenticated"),
        ("/me with token", client.get("/me", headers={"Authorization": f"Bearer {token}"}), 200, STUDENT[0]),
        ("/me with invalid token", client.get("/me", headers={"Authorization": "Bearer invalid"}), 401, "Invalid or expired token"),
    ]

checks = []
for label, response, status, expected in cases:
    data = response.json()
    challenge = response.headers.get("www-authenticate")
    passed = response.status_code == status
    if status == 401:
        passed &= (
            challenge == "Bearer"
            and response.headers["content-type"].startswith("application/problem+json")
            and data.get("detail") == expected
        )
    elif response is good:
        passed &= bool(token) and data.get("token_type") == expected
    else:
        passed &= data == {"id": 2, "email": expected, "role": "student", "studentId": 1}
    checks.append(passed)
    print(f"{'ok  ' if passed else 'FAIL'} {label:<24} {response.status_code}  WWW-Authenticate: {challenge or '-'}")
finish(checks)
