"""Tests for fee and payment operations."""

from decimal import Decimal

from fastapi.testclient import TestClient


def test_create_fee(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test admin can create a fee."""
    response = client.post(
        "/fees",
        headers=admin_headers,
        json={
            "student_id": test_student.id,
            "title": "Tuition Fee",
            "description": "Monthly tuition",
            "total_amount": "60000.00",
            "due_date": "2026-12-31",  # Future date to avoid overdue status
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == test_student.id
    assert data["title"] == "Tuition Fee"
    assert Decimal(data["total_amount"]) == Decimal("60000.00")
    assert Decimal(data["paid_amount"]) == Decimal("0.00")
    assert Decimal(data["balance"]) == Decimal("60000.00")
    assert data["status"] == "unpaid"


def test_get_fee_by_id(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test getting a fee by ID."""
    response = client.get(f"/fees/{test_fee.id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_fee.id
    assert data["title"] == test_fee.title


def test_get_fees(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test getting all fees."""
    response = client.get("/fees", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total_items"] >= 1


def test_record_payment(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test recording a payment."""
    response = client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "20000.00",
            "payment_date": "2025-01-15",
            "payment_method": "cash",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["amount"]) == Decimal("20000.00")
    assert data["student_fee_id"] == test_fee.id


def test_payment_updates_fee_status(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test that payment updates fee status correctly."""
    # Record partial payment
    client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "20000.00",
            "payment_date": "2026-01-15",
            "payment_method": "cash",
        },
    )
    
    # Check fee status
    response = client.get(f"/fees/{test_fee.id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["paid_amount"]) == Decimal("20000.00")
    assert Decimal(data["balance"]) == Decimal("40000.00")
    assert data["status"] == "partial"


def test_full_payment(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test full payment."""
    # Record first payment
    client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "30000.00",
            "payment_date": "2026-01-15",
            "payment_method": "cash",
        },
    )
    
    # Record remaining payment
    response = client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "30000.00",
            "payment_date": "2026-01-16",
            "payment_method": "upi",
        },
    )
    assert response.status_code == 201
    
    # Check fee status
    fee_response = client.get(f"/fees/{test_fee.id}", headers=admin_headers)
    data = fee_response.json()
    assert Decimal(data["paid_amount"]) == Decimal("60000.00")
    assert Decimal(data["balance"]) == Decimal("0.00")
    assert data["status"] == "paid"


def test_overpayment_fails(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test overpayment is rejected."""
    response = client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "70000.00",  # more than fee amount
            "payment_date": "2026-01-15",
            "payment_method": "cash",
        },
    )
    assert response.status_code == 409
    assert "exceed" in response.json()["detail"].lower()


def test_zero_payment_fails(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test zero payment is rejected."""
    response = client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "0.00",
            "payment_date": "2026-01-15",
            "payment_method": "cash",
        },
    )
    assert response.status_code == 422


def test_negative_payment_fails(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test negative payment is rejected."""
    response = client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "-100.00",
            "payment_date": "2026-01-15",
            "payment_method": "cash",
        },
    )
    assert response.status_code == 422


def test_delete_fee_without_payments(client: TestClient, admin_headers: dict, test_student) -> None:
    """Test deleting fee without payments."""
    # Create fee
    create_response = client.post(
        "/fees",
        headers=admin_headers,
        json={
            "student_id": test_student.id,
            "title": "Deletable Fee",
            "total_amount": "5000.00",
            "due_date": "2025-12-31",
        },
    )
    assert create_response.status_code == 201
    fee_id = create_response.json()["id"]
    
    # Delete
    response = client.delete(f"/fees/{fee_id}", headers=admin_headers)
    assert response.status_code == 204


def test_delete_fee_with_payments_fails(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test deleting fee with payments returns 409."""
    # Record a payment
    client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "1000.00",
            "payment_date": "2026-01-15",
            "payment_method": "cash",
        },
    )
    
    # Try to delete
    response = client.delete(f"/fees/{test_fee.id}", headers=admin_headers)
    assert response.status_code == 409
    assert "payments" in response.json()["detail"].lower()


def test_update_fee_total_below_paid_fails(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test updating fee total below paid amount fails."""
    # Record payment
    client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "30000.00",
            "payment_date": "2026-01-15",
            "payment_method": "cash",
        },
    )
    
    # Try to reduce total below paid
    response = client.put(
        f"/fees/{test_fee.id}",
        headers=admin_headers,
        json={
            "total_amount": "20000.00",
        },
    )
    assert response.status_code == 409
    assert "cannot be less than" in response.json()["detail"].lower()


def test_get_payment_history(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test getting payment history."""
    # Record multiple payments
    client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "10000.00",
            "payment_date": "2026-01-15",
            "payment_method": "cash",
        },
    )
    
    client.post(
        f"/fees/{test_fee.id}/payments",
        headers=admin_headers,
        json={
            "amount": "15000.00",
            "payment_date": "2026-01-16",
            "payment_method": "upi",
        },
    )
    
    # Get payments
    response = client.get(f"/fees/{test_fee.id}/payments", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert Decimal(data[0]["amount"]) == Decimal("15000.00")  # newest first
    assert Decimal(data[1]["amount"]) == Decimal("10000.00")


def test_get_fee_summary(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test getting fee summary."""
    response = client.get("/fees/summary", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_assigned" in data
    assert "total_collected" in data
    assert "total_pending" in data
    assert "unpaid_count" in data
    assert "partial_count" in data
    assert "paid_count" in data
    assert "overdue_count" in data


def test_filter_fees_by_status(client: TestClient, admin_headers: dict, test_fee) -> None:
    """Test filtering fees by status."""
    response = client.get("/fees?status=unpaid", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    for fee in data["items"]:
        assert fee["status"] == "unpaid"


def test_fee_pagination(client: TestClient, admin_headers: dict) -> None:
    """Test fee pagination."""
    response = client.get("/fees?page=1&page_size=5", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_items" in data
    assert "total_pages" in data