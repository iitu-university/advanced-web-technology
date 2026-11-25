"""Compare failed login times with the dummy Argon2id verification active."""

from statistics import median
from time import perf_counter

import httpx

from lab9_checks import BASE, STUDENT, login

ATTEMPTS = 40
PASSWORD = "intentionally-wrong"
EMAILS = {"unknown email": "nobody@example.com", "known email": STUDENT[0]}
times: dict[str, list[float]] = {label: [] for label in EMAILS}

with httpx.Client(base_url=BASE) as client:
    for email in EMAILS.values():
        assert login(client, email, PASSWORD).status_code == 401
    for _ in range(ATTEMPTS):
        for label, email in EMAILS.items():
            start = perf_counter()
            response = login(client, email, PASSWORD)
            elapsed = (perf_counter() - start) * 1000
            assert response.status_code == 401
            times[label].append(elapsed)

print(f"Wrong password, {ATTEMPTS} requests per case")
for label, samples in times.items():
    print(f"{label:<14} median {median(samples):6.1f} ms")
