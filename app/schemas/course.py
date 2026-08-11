import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class CourseBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    duration_months: int | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        """Validate and normalize course code."""
        if not value or not value.strip():
            raise ValueError("Course code is required.")

        normalized = value.strip()

        if len(normalized) < 2 or len(normalized) > 50:
            raise ValueError("Course code must be between 2 and 50 characters.")

        normalized = normalized.upper()

        if not re.match(r'^[A-Z0-9\-_]+$', normalized):
            raise ValueError("Course code can only contain letters, numbers, hyphens, and underscores.")

        return normalized

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate and normalize course name."""
        if not value or not value.strip():
            raise ValueError("Course name is required.")

        normalized = value.strip()

        if len(normalized) < 3 or len(normalized) > 150:
            raise ValueError("Course name must be between 3 and 150 characters.")

        return normalized

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        """Validate and normalize description."""
        if value is None or value.strip() == "":
            return None

        normalized = value.strip()

        if len(normalized) > 500:
            raise ValueError("Description must be 500 characters or less.")

        return normalized

    @field_validator("duration_months")
    @classmethod
    def validate_duration_months(cls, value: int | None) -> int | None:
        """Validate duration months."""
        if value is None:
            return None

        if value <= 0:
            raise ValueError("Duration must be a positive integer.")

        if value > 120:
            raise ValueError("Duration cannot exceed 120 months.")

        return value


class CourseCreate(CourseBase):
    is_active: bool = True


class CourseUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    duration_months: int | None = None
    is_active: bool | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str | None) -> str | None:
        """Validate and normalize course code."""
        if value is None:
            return None

        if not value or not value.strip():
            raise ValueError("Course code is required.")

        normalized = value.strip()

        if len(normalized) < 2 or len(normalized) > 50:
            raise ValueError("Course code must be between 2 and 50 characters.")

        normalized = normalized.upper()

        if not re.match(r'^[A-Z0-9\-_]+$', normalized):
            raise ValueError("Course code can only contain letters, numbers, hyphens, and underscores.")

        return normalized

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        """Validate and normalize course name."""
        if value is None:
            return None

        if not value or not value.strip():
            raise ValueError("Course name is required.")

        normalized = value.strip()

        if len(normalized) < 3 or len(normalized) > 150:
            raise ValueError("Course name must be between 3 and 150 characters.")

        return normalized

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        """Validate and normalize description."""
        if value is None or value.strip() == "":
            return None

        normalized = value.strip()

        if len(normalized) > 500:
            raise ValueError("Description must be 500 characters or less.")

        return normalized

    @field_validator("duration_months")
    @classmethod
    def validate_duration_months(cls, value: int | None) -> int | None:
        """Validate duration months."""
        if value is None:
            return None

        if value <= 0:
            raise ValueError("Duration must be a positive integer.")

        if value > 120:
            raise ValueError("Duration cannot exceed 120 months.")

        return value


class CourseResponse(CourseBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
