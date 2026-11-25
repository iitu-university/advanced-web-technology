from sqlalchemy import select

from db import SessionLocal
from models import User
from security import password_hash
from seed_users import USERS

with SessionLocal() as db:
    users = {user.email: user for user in db.scalars(select(User))}

checks = {
    "four accounts": len(users) == len(USERS),
    "roles and links": all(
        email in users and (users[email].role, users[email].student_id) == (role, student_id)
        for email, role, student_id, _ in USERS
    ),
    "Argon2id hashes": all(user.password_hash.startswith("$argon2id$") for user in users.values()),
    "correct demo passwords": all(
        email in users and password_hash.verify(password, users[email].password_hash)
        for email, _, _, password in USERS
    ),
}
for label, passed in checks.items():
    print(f"{'ok  ' if passed else 'FAIL'} {label}")
print(f"{sum(checks.values())} of {len(checks)} as expected")
raise SystemExit(0 if all(checks.values()) else 1)
