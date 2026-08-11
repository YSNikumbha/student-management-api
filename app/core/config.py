from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    database_url: str = "sqlite:///./student_management.db"
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    environment: str = "development"
    app_name: str = "Student Management API"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str, info) -> str:
        environment = info.data.get("environment", "development")
        if environment == "production" and (not value or value == "replace-with-a-long-random-secret"):
            raise ValueError(
                "SECRET_KEY must be set to a secure value in production. "
                "Generate a strong random secret and set it via environment variable."
            )
        return value


settings = Settings()
