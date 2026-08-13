"""Tests for deployment-sensitive configuration validation."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_postgresql_url_is_normalized_for_psycopg() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgres://user:password@example.com:5432/student_management",
        environment="production",
        secret_key="x" * 64,
        cors_origins="https://school.example,http://localhost:5173/",
    )

    assert settings.database_url == "postgresql+psycopg://user:password@example.com:5432/student_management"
    assert settings.cors_origins == ["https://school.example", "http://localhost:5173"]


@pytest.mark.parametrize(
    "secret_key",
    ["", "secret", "changeme", "replace-with-a-long-random-secret", "test-secret-key-for-testing-only"],
)
def test_production_rejects_missing_or_placeholder_secret(secret_key: str) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="sqlite:///./test.db",
            environment="production",
            secret_key=secret_key,
        )


def test_production_rejects_short_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="sqlite:///./test.db",
            environment="production",
            secret_key="short-production-secret",
        )


def test_production_rejects_wildcard_cors_origin() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="sqlite:///./test.db",
            environment="production",
            secret_key="x" * 64,
            cors_origins="*",
        )
