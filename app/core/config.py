from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./student_management.db"
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    environment: str = "development"
    app_name: str = "Student Management API"
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        database_url = value.strip()
        if database_url.startswith("postgres://"):
            return "postgresql+psycopg://" + database_url.removeprefix("postgres://")
        if database_url.startswith("postgresql://"):
            return "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
        return database_url

    @field_validator("environment")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return (value or "development").strip().lower()

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return [str(origin).strip().rstrip("/") for origin in value if str(origin).strip()]
        raise TypeError("CORS_ORIGINS must be a comma-separated string or list")

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment != "production":
            return self

        secret = self.secret_key.strip()
        normalized_secret = secret.lower()
        placeholder_values = {
            "changeme",
            "change-me",
            "secret",
            "dev-secret",
            "development",
            "password",
            "replace-with-a-long-random-secret",
            "test-secret-key-for-testing-only",
            "local-compose-development-secret-change-me",
        }
        placeholder_fragments = (
            "changeme",
            "change-me",
            "replace-with",
            "development default",
            "test-secret",
            "local-compose",
        )
        if (
            not secret
            or len(secret) < 32
            or normalized_secret in placeholder_values
            or any(fragment in normalized_secret for fragment in placeholder_fragments)
        ):
            raise ValueError(
                "SECRET_KEY must be set to a secure value in production. "
                "Generate a strong random secret and set it via environment variable."
            )

        if "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS cannot include '*' in production.")

        return self


settings = Settings()
