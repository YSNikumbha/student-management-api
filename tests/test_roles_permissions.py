from fastapi import status
from fastapi.testclient import TestClient


def test_admin_can_view_roles_permissions(client: TestClient, admin_headers: dict) -> None:
    response = client.get("/roles-permissions", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["roles"]
    assert any(permission["code"] == "users.view" for permission in data["permissions"])


def test_staff_cannot_manage_roles(client: TestClient, staff_headers: dict) -> None:
    response = client.post(
        "/roles-permissions/roles",
        headers=staff_headers,
        json={"name": "demo custom", "display_name": "Demo Custom", "permission_codes": []},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_role_create_and_permission_update(client: TestClient, admin_headers: dict) -> None:
    create_response = client.post(
        "/roles-permissions/roles",
        headers=admin_headers,
        json={
            "name": "report analyst",
            "display_name": "Report Analyst",
            "description": "Can view and export reports",
            "permission_codes": ["dashboard.view", "reports.view"],
        },
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    role = create_response.json()
    assert "reports.view" in role["permission_codes"]

    update_response = client.put(
        f"/roles-permissions/roles/{role['id']}/permissions",
        headers=admin_headers,
        json={"permission_codes": ["dashboard.view", "reports.view", "reports.export"]},
    )
    assert update_response.status_code == status.HTTP_200_OK
    assert "reports.export" in update_response.json()["permission_codes"]


def test_user_role_assignment_uses_permissions(client: TestClient, admin_headers: dict) -> None:
    roles_response = client.get("/roles-permissions", headers=admin_headers)
    teacher = next(role for role in roles_response.json()["roles"] if role["name"] == "teacher")
    user_response = client.post(
        "/users",
        headers=admin_headers,
        json={
            "name": "Permission Teacher",
            "email": "permission.teacher@example.com",
            "password": "Teacher123",
            "role": "teacher",
            "role_id": teacher["id"],
        },
    )
    assert user_response.status_code == status.HTTP_201_CREATED
    user = user_response.json()
    assert user["role"] == "teacher"
    assert "attendance.mark" in user["permissions"]


def test_unauthorized_user_management_access(client: TestClient, staff_headers: dict) -> None:
    response = client.get("/users", headers=staff_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
