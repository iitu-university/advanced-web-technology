"""Shared HTTP helpers for the Lab 9 checks against the local teaching API."""

import httpx

BASE = "http://localhost:8000"
STUDENT = ("aigerim@example.com", "aigerim-demo-pass")
ADMIN = ("admin@example.com", "admin-demo-password")


def login(client, email: str, password: str) -> httpx.Response:
    return client.post("/auth/login", data={"username": email, "password": password})


def authorization(client, credentials: tuple[str, str]) -> dict[str, str]:
    response = login(client, *credentials)
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def finish(checks: list[bool]) -> None:
    print(f"{sum(checks)} of {len(checks)} as expected")
    if not all(checks):
        raise SystemExit(1)
