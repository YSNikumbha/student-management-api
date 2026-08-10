from __future__ import annotations

import os
import sys
from getpass import getpass
from pathlib import Path

from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.database.database import SessionLocal  # noqa: E402
from app.schemas.user import UserCreate  # noqa: E402
from app.services import user_service  # noqa: E402


def prompt_value(label: str, env_name: str, secret: bool = False) -> str:
    value = os.getenv(env_name)
    if value:
        return value

    prompt = f"{label}: "
    return getpass(prompt) if secret else input(prompt).strip()


def create_admin() -> None:
    name = prompt_value("Admin name", "ADMIN_NAME")
    email = prompt_value("Admin email", "ADMIN_EMAIL")
    password = prompt_value("Admin password", "ADMIN_PASSWORD", secret=True)

    if not password:
        raise ValueError("Admin password is required.")

    try:
        user_data = UserCreate(
            name=name,
            email=email,
            password=password,
            role="admin",
        )
    except ValidationError as error:
        print(error)
        raise SystemExit(1) from error

    db = SessionLocal()
    try:
        existing_user = user_service.get_user_by_email(db, user_data.email)
        if existing_user is not None:
            print(f"User with email {user_data.email} already exists.")
            return

        user = user_service.create_user(db, user_data)
        print(f"Created admin user: {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
