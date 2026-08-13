from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _validate_name(value: str) -> str:
    trimmed = value.strip()
    if len(trimmed) < 2 or len(trimmed) > 150:
        raise ValueError("Name must be between 2 and 150 characters")
    return trimmed


def _validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if len(value) > 128:
        raise ValueError("Password must be 128 characters or fewer")
    if not any(character.isalpha() for character in value):
        raise ValueError("Password must include at least one letter")
    if not any(character.isdigit() for character in value):
        raise ValueError("Password must include at least one number")
    return value


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="teacher", min_length=2, max_length=50)
    role_id: int | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _validate_name(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_password(value)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()

    @field_validator("role")
    @classmethod
    def normalize_role(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "_").replace("-", "_")


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    role: str | None = Field(default=None, min_length=2, max_length=50)
    role_id: int | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_name(value)

    @field_validator("email")
    @classmethod
    def normalize_optional_email(cls, value: EmailStr | None) -> str | None:
        if value is None:
            return None
        return str(value).lower()

    @field_validator("role")
    @classmethod
    def normalize_optional_role(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().lower().replace(" ", "_").replace("-", "_")


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return _validate_password(value)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    role_id: int | None = None
    role_display_name: str | None = None
    permissions: list[str] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
