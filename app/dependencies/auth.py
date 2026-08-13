from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.database import get_db
from app.models.user import User
from app.services import role_permission_service, user_service


bearer_scheme = HTTPBearer(auto_error=False)
ADMIN_ROLE = "admin"
TEACHER_ROLE = "teacher"
ACCOUNTANT_ROLE = "accountant"
STAFF_ROLE = "staff"

ATTENDANCE_EDITOR_ROLES = {ADMIN_ROLE, TEACHER_ROLE, STAFF_ROLE}
FEE_MANAGER_ROLES = {ADMIN_ROLE, ACCOUNTANT_ROLE}
PAYMENT_RECORDER_ROLES = {ADMIN_ROLE, ACCOUNTANT_ROLE, STAFF_ROLE}
GENERAL_REPORT_ROLES = {ADMIN_ROLE, TEACHER_ROLE, STAFF_ROLE}
FEE_REPORT_ROLES = {ADMIN_ROLE, TEACHER_ROLE, ACCOUNTANT_ROLE, STAFF_ROLE}


def _unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized_exception()

    try:
        payload = decode_access_token(credentials.credentials)
        email = payload.get("sub")
        if not isinstance(email, str) or not email:
            raise _unauthorized_exception()
    except JWTError as error:
        raise _unauthorized_exception() from error

    user = user_service.get_user_by_email(db, email)
    if user is None:
        raise _unauthorized_exception()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive",
        )

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != ADMIN_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


def require_permission(permission_code: str):
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if not role_permission_service.user_has_permission(db, current_user, permission_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission_code}",
            )
        return current_user

    return dependency


def require_roles(*roles: str):
    allowed_roles = set(roles)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return dependency


def require_attendance_editor(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if (
        current_user.role not in ATTENDANCE_EDITOR_ROLES
        and not role_permission_service.user_has_permission(db, current_user, "attendance.mark")
        and not role_permission_service.user_has_permission(db, current_user, "attendance.edit")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Attendance access required",
        )
    return current_user


def require_fee_manager(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if (
        current_user.role not in FEE_MANAGER_ROLES
        and not role_permission_service.user_has_permission(db, current_user, "fees.create")
        and not role_permission_service.user_has_permission(db, current_user, "fees.edit")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fee management access required",
        )
    return current_user


def require_payment_recorder(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if (
        current_user.role not in PAYMENT_RECORDER_ROLES
        and not role_permission_service.user_has_permission(db, current_user, "fees.record_payment")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Payment access required",
        )
    return current_user


def require_general_report_reader(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if (
        current_user.role not in GENERAL_REPORT_ROLES
        and (
            current_user.role == ACCOUNTANT_ROLE
            or not role_permission_service.user_has_permission(db, current_user, "reports.view")
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Report access required",
        )
    return current_user


def require_fee_report_reader(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if (
        current_user.role not in FEE_REPORT_ROLES
        and not role_permission_service.user_has_permission(db, current_user, "reports.view")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fee report access required",
        )
    return current_user
