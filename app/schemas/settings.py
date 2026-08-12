from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SystemSettingUpdate(BaseModel):
    school_name: str | None = Field(default=None, min_length=2, max_length=200)
    official_email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    logo_path: str | None = Field(default=None, max_length=500)
    default_academic_year_id: int | None = None
    currency: str | None = Field(default=None, min_length=2, max_length=10)
    timezone: str | None = Field(default=None, min_length=2, max_length=80)
    language: str | None = Field(default=None, min_length=2, max_length=50)


class SystemSettingResponse(BaseModel):
    id: int
    school_name: str
    official_email: str | None = None
    phone: str | None = None
    address: str | None = None
    logo_path: str | None = None
    default_academic_year_id: int | None = None
    currency: str
    timezone: str
    language: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceUpdate(BaseModel):
    fee_alerts: bool | None = None
    attendance_alerts: bool | None = None
    system_notifications: bool | None = None


class NotificationPreferenceResponse(BaseModel):
    id: int
    user_id: int
    fee_alerts: bool
    attendance_alerts: bool
    system_notifications: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
