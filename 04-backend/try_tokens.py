"""Exercise the JWT verifier with isolated, application-issued fixtures."""

from datetime import datetime, timedelta, timezone
from secrets import token_hex
from unittest.mock import patch

import jwt

import security
from lab9_checks import finish

now = datetime.now(timezone.utc).replace(microsecond=0)


def issue(user_id: int = 2, issued_at: datetime = now) -> str:
    with patch("security.datetime") as clock:
        clock.now.return_value = issued_at
        return security.create_access_token(user_id)


def accepts(token: str) -> bool:
    try:
        security.read_access_token(token)
    except jwt.InvalidTokenError:
        return False
    return True


with patch.object(security.settings, "secret_key", token_hex(32)):
    valid = issue()
    with patch.object(security.settings, "secret_key", token_hex(32)):
        rotated_key_token = issue()
    with patch.object(security, "ISSUER", "separate-test-service"):
        different_issuer_token = issue()

    claims = jwt.decode(
        valid, security.settings.secret_key, algorithms=[security.ALGORITHM], issuer=security.ISSUER
    )
    cases = {
        "valid token": security.read_access_token(valid) == 2,
        "expected claims and configured lifetime": set(claims) == {"sub", "iss", "iat", "exp"}
        and claims["sub"] == "2"
        and claims["exp"] - claims["iat"] == security.settings.access_token_minutes * 60,
        "expired token rejected": not accepts(issue(issued_at=now - timedelta(days=1))),
        "future issue time rejected": not accepts(issue(issued_at=now + timedelta(minutes=1))),
        "previous signing key rejected": not accepts(rotated_key_token),
        "different issuer rejected": not accepts(different_issuer_token),
        "zero subject rejected": not accepts(issue(0)),
        "out-of-range subject rejected": not accepts(issue(2**63)),
        "malformed input rejected": not accepts("invalid"),
    }

for label, passed in cases.items():
    print(f"{'ok  ' if passed else 'FAIL'} {label}")
finish(list(cases.values()))
