from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.audit_log import AuditLog
from app.schemas.pagination import get_offset

SENSITIVE_KEY_PARTS = (
    "password",
    "token",
    "jwt",
    "secret",
    "credential",
    "hashed",
    "hash",
    "authorization",
)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def _sanitize_metadata(value: Any) -> Any:
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_string = str(key)
            if _is_sensitive_key(key_string):
                continue
            sanitized[key_string] = _sanitize_metadata(item)
        return sanitized

    if isinstance(value, list):
        return [_sanitize_metadata(item) for item in value]

    if isinstance(value, tuple):
        return [_sanitize_metadata(item) for item in value]

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    return value


def get_request_ip(request: Any) -> str | None:
    client = getattr(request, "client", None)
    host = getattr(client, "host", None)
    return str(host) if host else None


def record_audit_event(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | str | None = None,
    description: str,
    metadata_json: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog | None:
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            description=description[:1000],
            metadata_json=_sanitize_metadata(metadata_json) if metadata_json else None,
            ip_address=ip_address,
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log
    except Exception:
        db.rollback()
        return None


def get_audit_logs_paginated(
    db: Session,
    *,
    user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[AuditLog], int]:
    statement = select(AuditLog).options(selectinload(AuditLog.user))

    if user_id is not None:
        statement = statement.where(AuditLog.user_id == user_id)

    if action:
        statement = statement.where(AuditLog.action == action)

    if entity_type:
        statement = statement.where(AuditLog.entity_type == entity_type)

    if start_date is not None:
        start_datetime = datetime.combine(start_date, time.min)
        statement = statement.where(AuditLog.created_at >= start_datetime)

    if end_date is not None:
        end_datetime = datetime.combine(end_date, time.max)
        statement = statement.where(AuditLog.created_at <= end_datetime)

    if search:
        pattern = f"%{search.lower()}%"
        statement = statement.where(
            or_(
                func.lower(AuditLog.action).like(pattern),
                func.lower(AuditLog.entity_type).like(pattern),
                func.lower(AuditLog.description).like(pattern),
            )
        )

    count_statement = select(func.count()).select_from(
        statement.with_only_columns(AuditLog.id).order_by(None).subquery(),
    )
    total_items = db.execute(count_statement).scalar_one()

    statement = (
        statement.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset(get_offset(page, page_size))
        .limit(page_size)
    )
    return list(db.execute(statement).scalars().all()), total_items


def build_audit_log_response(audit_log: AuditLog) -> dict[str, Any]:
    return {
        "id": audit_log.id,
        "user_id": audit_log.user_id,
        "user_name": audit_log.user.name if audit_log.user else None,
        "user_email": audit_log.user.email if audit_log.user else None,
        "action": audit_log.action,
        "entity_type": audit_log.entity_type,
        "entity_id": audit_log.entity_id,
        "description": audit_log.description,
        "metadata_json": audit_log.metadata_json,
        "ip_address": audit_log.ip_address,
        "created_at": audit_log.created_at,
    }
