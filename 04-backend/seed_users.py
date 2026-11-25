"""Populate the teaching database with four demo accounts."""

from sqlalchemy import text

from db import SessionLocal
from models import User
from security import password_hash

USERS = (
    ("admin@example.com", "admin", None, "admin-demo-password"),
    ("aigerim@example.com", "student", 1, "aigerim-demo-pass"),
    ("daniyar@example.com", "student", 2, "daniyar-demo-pass"),
    ("asel@example.com", "student", 3, "asel-demo-password"),
)


def seed_users() -> None:
    accounts = [
        User(email=email, role=role, student_id=student_id, password_hash=password_hash.hash(password))
        for email, role, student_id, password in USERS
    ]
    with SessionLocal.begin() as db:
        db.execute(text("TRUNCATE users RESTART IDENTITY"))
        db.add_all(accounts)


if __name__ == "__main__":
    seed_users()
    print(f"created users: {len(USERS)}")
