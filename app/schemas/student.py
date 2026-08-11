import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class StudentBase(BaseModel):
    student_code: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    date_of_birth: date | None = None
    course_id: int | None = None

    @field_validator("student_code")
    @classmethod
    def validate_student_code(cls, value: str) -> str:
        """Validate and normalize student code."""
        if not value or not value.strip():
            raise ValueError("Student code is required.")
        
        # Trim whitespace
        normalized = value.strip()
        
        # Check length
        if len(normalized) < 2 or len(normalized) > 50:
            raise ValueError("Student code must be between 2 and 50 characters.")
        
        # Uppercase normalization
        normalized = normalized.upper()
        
        # Allow only letters, numbers, hyphens, and underscores
        import re
        if not re.match(r'^[A-Z0-9\-_]+$', normalized):
            raise ValueError("Student code can only contain letters, numbers, hyphens, and underscores.")
        
        return normalized

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate and normalize name fields."""
        if not value or not value.strip():
            raise ValueError("Name is required.")
        
        # Trim whitespace
        normalized = value.strip()
        
        # Check length
        if len(normalized) < 2 or len(normalized) > 100:
            raise ValueError("Name must be between 2 and 100 characters.")
        
        # Allow letters (including Unicode), spaces, apostrophes, hyphens
        # Use a pattern that works with Python's re module
        import re
        # Match: letters (any Unicode), spaces, apostrophes, hyphens
        if not re.match(r'^[^\W\d_]+[\w\s\'-]*$', normalized, re.UNICODE):
            # More permissive fallback: just check for invalid chars
            if re.search(r'[0-9]', normalized):
                raise ValueError("Name cannot contain numbers.")
            if re.search(r'[^a-zA-Z\s\'-]', normalized):
                # Check if it's a Unicode letter (non-ASCII)
                if not all(c.isalpha() or c in " '-" for c in normalized):
                    raise ValueError("Name contains invalid characters.")
        
        return normalized

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize email to lowercase."""
        return value.strip().lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        """Validate phone number format."""
        if value is None or value.strip() == "":
            return None
        
        # Trim whitespace
        normalized = value.strip()
        
        # Remove all non-digit characters except leading +
        cleaned = re.sub(r'[^\d+]', '', normalized)
        
        # Check if it starts with +
        has_plus = cleaned.startswith('+')
        
        # Remove + for digit counting
        digits_only = cleaned.replace('+', '')
        
        # Validate digit count (10-15 digits)
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError("Phone must be 10 to 15 digits.")
        
        # Validate format with +
        if has_plus:
            if not re.match(r'^\+[\d]{10,15}$', cleaned):
                raise ValueError("Phone format is invalid. Use +1234567890 or 1234567890.")
        
        return cleaned

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        """Validate date of birth is not in the future."""
        if value is None:
            return None
        
        from datetime import datetime
        today = datetime.now().date()
        
        if value > today:
            raise ValueError("Date of birth cannot be in the future.")
        
        return value


class StudentCreate(StudentBase):
    status: Literal["active", "inactive"] = "active"


class StudentUpdate(BaseModel):
    student_code: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    course_id: int | None = None
    status: Literal["active", "inactive"] | None = None

    @field_validator("student_code")
    @classmethod
    def validate_student_code(cls, value: str | None) -> str | None:
        """Validate and normalize student code."""
        if value is None:
            return None
        
        if not value or not value.strip():
            raise ValueError("Student code is required.")
        
        # Trim whitespace
        normalized = value.strip()
        
        # Check length
        if len(normalized) < 2 or len(normalized) > 50:
            raise ValueError("Student code must be between 2 and 50 characters.")
        
        # Uppercase normalization
        normalized = normalized.upper()
        
        # Allow only letters, numbers, hyphens, and underscores
        import re
        if not re.match(r'^[A-Z0-9\-_]+$', normalized):
            raise ValueError("Student code can only contain letters, numbers, hyphens, and underscores.")
        
        return normalized

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        """Validate and normalize name fields."""
        if value is None:
            return None
        
        if not value or not value.strip():
            raise ValueError("Name is required.")
        
        # Trim whitespace
        normalized = value.strip()
        
        # Check length
        if len(normalized) < 2 or len(normalized) > 100:
            raise ValueError("Name must be between 2 and 100 characters.")
        
        # Allow letters (including Unicode), spaces, apostrophes, hyphens
        import re
        # Check for numbers (not allowed)
        if re.search(r'[0-9]', normalized):
            raise ValueError("Name cannot contain numbers.")
        # Check for other invalid characters (allow letters, spaces, apostrophes, hyphens)
        if not all(c.isalpha() or c in " '-" for c in normalized):
            raise ValueError("Name contains invalid characters.")
        
        return normalized

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        """Normalize email to lowercase."""
        if value is None:
            return None
        return value.strip().lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        """Validate phone number format."""
        if value is None or value.strip() == "":
            return None
        
        # Trim whitespace
        normalized = value.strip()
        
        # Remove all non-digit characters except leading +
        import re
        cleaned = re.sub(r'[^\d+]', '', normalized)
        
        # Check if it starts with +
        has_plus = cleaned.startswith('+')
        
        # Remove + for digit counting
        digits_only = cleaned.replace('+', '')
        
        # Validate digit count (10-15 digits)
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError("Phone must be 10 to 15 digits.")
        
        # Validate format with +
        if has_plus:
            if not re.match(r'^\+[\d]{10,15}$', cleaned):
                raise ValueError("Phone format is invalid. Use +1234567890 or 1234567890.")
        
        return cleaned

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        """Validate date of birth is not in the future."""
        if value is None:
            return None
        
        from datetime import datetime
        today = datetime.now().date()
        
        if value > today:
            raise ValueError("Date of birth cannot be in the future.")
        
        return value


class StudentResponse(StudentBase):
    id: int
    status: Literal["active", "inactive"]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)