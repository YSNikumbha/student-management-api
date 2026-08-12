from fastapi.testclient import TestClient


def _headers_for(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_teacher(client: TestClient, admin_headers: dict, email: str) -> dict:
    response = client.post(
        "/users",
        headers=admin_headers,
        json={
            "name": "Notification Teacher",
            "email": email,
            "role": "teacher",
            "password": "Teacher123",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_account_created_notification_goes_to_new_user_only(
    client: TestClient,
    admin_headers: dict,
) -> None:
    created_user = _create_teacher(client, admin_headers, "notify.teacher@test.com")
    teacher_headers = _headers_for(client, created_user["email"], "Teacher123")

    teacher_response = client.get("/notifications", headers=teacher_headers)
    assert teacher_response.status_code == 200
    teacher_titles = [item["title"] for item in teacher_response.json()["items"]]
    assert "Account created" in teacher_titles

    admin_response = client.get("/notifications", headers=admin_headers)
    assert admin_response.status_code == 200
    admin_messages = [item["message"] for item in admin_response.json()["items"]]
    assert all(created_user["email"] not in message for message in admin_messages)


def test_unread_count_and_mark_read(
    client: TestClient,
    admin_headers: dict,
) -> None:
    created_user = _create_teacher(client, admin_headers, "read.teacher@test.com")
    teacher_headers = _headers_for(client, created_user["email"], "Teacher123")

    count_response = client.get("/notifications/unread-count", headers=teacher_headers)
    assert count_response.status_code == 200
    assert count_response.json()["unread_count"] == 1

    list_response = client.get("/notifications", headers=teacher_headers)
    notification_id = list_response.json()["items"][0]["id"]

    read_response = client.put(
        f"/notifications/{notification_id}/read",
        headers=teacher_headers,
    )
    assert read_response.status_code == 200
    assert read_response.json()["is_read"] is True

    count_after = client.get("/notifications/unread-count", headers=teacher_headers)
    assert count_after.status_code == 200
    assert count_after.json()["unread_count"] == 0


def test_mark_all_read(
    client: TestClient,
    admin_headers: dict,
) -> None:
    created_user = _create_teacher(client, admin_headers, "allread.teacher@test.com")
    teacher_headers = _headers_for(client, created_user["email"], "Teacher123")

    reset_response = client.post(
        f"/users/{created_user['id']}/reset-password",
        headers=admin_headers,
        json={"new_password": "Teacher456"},
    )
    assert reset_response.status_code == 200

    mark_all_response = client.put("/notifications/read-all", headers=teacher_headers)
    assert mark_all_response.status_code == 200
    assert mark_all_response.json()["updated"] >= 1

    count_response = client.get("/notifications/unread-count", headers=teacher_headers)
    assert count_response.json()["unread_count"] == 0


def test_password_reset_notification(
    client: TestClient,
    admin_headers: dict,
) -> None:
    created_user = _create_teacher(client, admin_headers, "reset.notify@test.com")

    reset_response = client.post(
        f"/users/{created_user['id']}/reset-password",
        headers=admin_headers,
        json={"new_password": "Teacher456"},
    )
    assert reset_response.status_code == 200

    teacher_headers = _headers_for(client, created_user["email"], "Teacher456")
    list_response = client.get("/notifications", headers=teacher_headers)
    assert list_response.status_code == 200
    titles = [item["title"] for item in list_response.json()["items"]]
    assert "Password reset" in titles


def test_notification_auth_and_current_user_scope(
    client: TestClient,
    admin_headers: dict,
) -> None:
    created_user = _create_teacher(client, admin_headers, "scoped.teacher@test.com")
    teacher_headers = _headers_for(client, created_user["email"], "Teacher123")

    unauthenticated_response = client.get("/notifications")
    assert unauthenticated_response.status_code == 401

    teacher_list = client.get("/notifications", headers=teacher_headers)
    notification_id = teacher_list.json()["items"][0]["id"]

    admin_mark_response = client.put(
        f"/notifications/{notification_id}/read",
        headers=admin_headers,
    )
    assert admin_mark_response.status_code == 404
