from sqlalchemy import text

from db import engine


def main() -> None:
    with engine.connect() as conn:
        name, user = conn.execute(text("SELECT current_database(), current_user")).one()
        version = conn.execute(text("SHOW server_version")).scalar_one()
    print(f"connected to {name} as {user}, PostgreSQL {version}")


if __name__ == "__main__":
    main()
