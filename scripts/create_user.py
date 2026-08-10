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


VALID_ROLES = {"admin", "staff"}


def prompt_value(label: str, env_name: str, secret: bool = False) -> str:
    value = os.getenv(env_name)
    if value:
        return value

    prompt = f"{label}: "
    return getpass(prompt) if secret else input(prompt).strip()


def normalize_role(role: str) -> str:
    normalized_role = role.strip().lower()
    if normalized_role not in VALID_ROLES:
        raise ValueError("Role must be either 'admin' or 'staff'.")
    return normalized_role


def create_user(role: str | None = None) -> None:
    selected_role = normalize_role(role or os.getenv("USER_ROLE", "staff"))
    name = prompt_value("Name", "USER_NAME")
    email = prompt_value("Email", "USER_EMAIL")
    password = prompt_value("Password", "USER_PASSWORD", secret=True)

    if not password:
        raise ValueError("Password is required.")

    try:
        user_data = UserCreate(
            name=name,
            email=email,
            password=password,
            role=selected_role,
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
        print(f"Created {user.role} user: {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    cli_role = sys.argv[1] if len(sys.argv) > 1 else None
    create_user(cli_role)
