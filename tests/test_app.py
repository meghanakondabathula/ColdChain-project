
import pytest

# AUTHENTICATION TESTS
def test_dashboard_requires_login(client):
    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_shipment_api_requires_login(client):
    response = client.get("/api/shipments")

    assert response.status_code == 401


def test_dashboard_access_after_login(client, login_as):
    login_as("testadmin")

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    assert "shipments" in response.get_json()

# INVALID RESOURCE TESTS
def test_invalid_shipment(client, login_as):
    login_as("testadmin")

    response = client.get(
        "/api/shipments/NONEXISTENT-TEST-ID/details"
    )

    assert response.status_code == 404


def test_invalid_deviation(client, login_as):
    login_as("testadmin")

    response = client.get(
        "/api/deviations/999999999"
    )

    assert response.status_code == 404


# CSRF PROTECTION TEST
def test_missing_csrf_token(client, login_as):
    login_as("testadmin")

    response = client.post(
        "/api/deviations",
        json={"shipment_id": "TEST-SHIPMENT"}
    )

    assert response.status_code == 400


# ROLE PERMISSION TESTS
def test_viewer_cannot_create_deviation(
    client, login_as, csrf_headers
):
    login_as("testviewer")

    response = client.post(
        "/api/deviations",
        json={"shipment_id": "TEST-SHIPMENT"},
        headers=csrf_headers
    )

    assert response.status_code == 403


def test_viewer_cannot_update_deviation(
    client, login_as, csrf_headers
):
    login_as("testviewer")

    response = client.post(
        "/api/deviations/999999999/status",
        json={
            "status": "UNDER_INVESTIGATION",
            "notes": "Test update"
        },
        headers=csrf_headers
    )

    assert response.status_code == 403


def test_analyst_cannot_close_deviation(
    client, login_as, csrf_headers
):
    login_as("testanalyst")

    response = client.post(
        "/api/deviations/999999999/status",
        json={
            "status": "CLOSED",
            "notes": "Test closure",
            "root_cause": "Testing"
        },
        headers=csrf_headers
    )

    assert response.status_code == 403


def test_viewer_cannot_access_user_management(
    client, login_as
):
    login_as("testviewer")

    response = client.get("/users")

    assert response.status_code == 403


# PDF REPORT TESTS
def test_invalid_shipment_pdf(client, login_as):
    login_as("testadmin")

    response = client.get(
        "/api/shipments/NONEXISTENT-TEST-ID/report"
    )

    assert response.status_code == 404


def test_invalid_deviation_pdf(client, login_as):
    login_as("testadmin")

    response = client.get(
        "/api/deviations/999999999/report"
    )

    assert response.status_code == 404


def test_invalid_audit_pdf(client, login_as):
    login_as("testadmin")

    response = client.get(
        "/api/deviations/999999999/audit-report"
    )

    assert response.status_code == 404


def test_valid_shipment_pdf(client, login_as):
    login_as("testadmin")

    shipment_response = client.get(
        "/api/shipments?page=1"
    )

    assert shipment_response.status_code == 200

    shipments = shipment_response.get_json()["shipments"]
    assert shipments, "Test dataset contains no shipments"

    shipment_id = shipments[0]["shipment_id"]

    response = client.get(
        f"/api/shipments/{shipment_id}/report"
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF-")


# AUDIT DATABASE INTEGRITY
def test_audit_event_is_immutable(test_environment):
    import sqlite3
    import deviation_manager

    deviation = deviation_manager.create_deviation(
        shipment_id="TEST-AUDIT-SHIPMENT",
        report_id="TEST-REPORT",
        decision="FAIL",
        actor="testadmin"
    )

    details = deviation_manager.get_deviation(
        deviation["deviation_id"]
    )

    event_id = details["events"][0]["event_id"]

    with pytest.raises(sqlite3.IntegrityError):
        with deviation_manager.connect() as conn:
            conn.execute(
                """
                UPDATE DeviationEvent
                SET notes = ?
                WHERE event_id = ?
                """,
                ("Modified audit event", event_id)
            )
