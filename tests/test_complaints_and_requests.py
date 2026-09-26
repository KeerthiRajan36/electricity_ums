def _create_customer(client, headers, suffix):
    return client.post("/api/v1/customers", json={
        "customer_number": f"CUST-C{suffix}", "full_name": "Complaint Test", "email": f"complaint{suffix}@example.com",
        "phone": "9000000002", "address": "3 Main St", "city": "Chennai"
    }, headers=headers).json()


def test_complaint_assignment_requires_available_technician(client, auth_headers):
    customer = _create_customer(client, auth_headers, "01")

    complaint = client.post("/api/v1/complaints", json={
        "customer_id": customer["id"], "complaint_type": "power_failure",
        "description": "No power", "priority": "high"
    }, headers=auth_headers).json()

    technician = client.post("/api/v1/technicians", json={
        "name": "Tech One", "employee_id": "EMP-C01", "phone": "9111111111", "specialization": "Electrical"
    }, headers=auth_headers).json()

    r = client.put(f"/api/v1/complaints/{complaint['id']}/assign", json={
        "technician_id": technician["id"]
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "assigned"

    # A second complaint cannot be assigned to the now-busy technician
    complaint2 = client.post("/api/v1/complaints", json={
        "customer_id": customer["id"], "complaint_type": "meter_issue",
        "description": "Meter display blank", "priority": "medium"
    }, headers=auth_headers).json()

    r2 = client.put(f"/api/v1/complaints/{complaint2['id']}/assign", json={
        "technician_id": technician["id"]
    }, headers=auth_headers)
    assert r2.status_code == 400

    # Resolving frees the technician up again
    r = client.put(f"/api/v1/complaints/{complaint['id']}/status", json={"status": "resolved"}, headers=auth_headers)
    assert r.status_code == 200

    r3 = client.put(f"/api/v1/complaints/{complaint2['id']}/assign", json={
        "technician_id": technician["id"]
    }, headers=auth_headers)
    assert r3.status_code == 200


def test_emergency_complaints_sort_first(client, auth_headers):
    customer = _create_customer(client, auth_headers, "02")
    client.post("/api/v1/complaints", json={
        "customer_id": customer["id"], "complaint_type": "other", "description": "Minor issue", "priority": "low"
    }, headers=auth_headers)
    client.post("/api/v1/complaints", json={
        "customer_id": customer["id"], "complaint_type": "power_failure",
        "description": "Total outage", "priority": "emergency"
    }, headers=auth_headers)

    r = client.get("/api/v1/complaints", headers=auth_headers)
    items = r.json()["items"]
    assert items[0]["priority"] == "emergency"


def test_suspended_customer_cannot_create_service_request(client, auth_headers):
    customer = _create_customer(client, auth_headers, "03")
    client.put(f"/api/v1/customers/{customer['id']}", json={"status": "suspended"}, headers=auth_headers)

    r = client.post("/api/v1/service-requests", json={
        "customer_id": customer["id"], "request_type": "name_change",
        "description": "Change my name on file", "requested_date": "2026-01-01"
    }, headers=auth_headers)
    assert r.status_code == 403


def test_service_request_approve_reject_flow(client, auth_headers):
    customer = _create_customer(client, auth_headers, "04")

    r = client.post("/api/v1/service-requests", json={
        "customer_id": customer["id"], "request_type": "address_change",
        "description": "Moving house", "requested_date": "2026-01-01"
    }, headers=auth_headers)
    request = r.json()

    r = client.put(f"/api/v1/service-requests/{request['id']}/approve", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    # Cannot reject something already approved (terminal state)
    r = client.put(f"/api/v1/service-requests/{request['id']}/reject", json={"reason": "changed my mind"},
                    headers=auth_headers)
    assert r.status_code == 400

    r = client.put(f"/api/v1/service-requests/{request['id']}/complete", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
