def _create_customer(client, headers, number="CUST-1001", email="cust1001@example.com"):
    return client.post("/api/v1/customers", json={
        "customer_number": number, "full_name": "Test Customer", "email": email,
        "phone": "9000000000", "address": "1 Main St", "city": "Chennai"
    }, headers=headers)


def test_create_customer_and_duplicate_number_rejected(client, auth_headers):
    r = _create_customer(client, auth_headers)
    assert r.status_code == 201

    r2 = _create_customer(client, auth_headers, email="different@example.com")  # same number
    assert r2.status_code == 409


def test_duplicate_email_rejected(client, auth_headers):
    _create_customer(client, auth_headers, number="CUST-2001", email="dupe@example.com")
    r = _create_customer(client, auth_headers, number="CUST-2002", email="dupe@example.com")
    assert r.status_code == 409


def test_create_connection_and_disconnect_blocks_billing(client, auth_headers):
    customer = _create_customer(client, auth_headers, number="CUST-3001", email="c3001@example.com").json()

    r = client.post("/api/v1/connections", json={
        "customer_id": customer["id"], "connection_number": "CONN-3001", "connection_type": "residential",
        "sanctioned_load": 5, "tariff_type": "Domestic", "connection_date": "2026-01-01"
    }, headers=auth_headers)
    assert r.status_code == 201
    connection = r.json()

    r = client.post(f"/api/v1/connections/{connection['id']}/disconnect", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "disconnected"

    r = client.post("/api/v1/bills/generate", json={
        "connection_id": connection["id"], "billing_month": "2026-02"
    }, headers=auth_headers)
    assert r.status_code == 400


def test_duplicate_connection_number_rejected(client, auth_headers):
    customer = _create_customer(client, auth_headers, number="CUST-4001", email="c4001@example.com").json()
    payload = {
        "customer_id": customer["id"], "connection_number": "CONN-DUP", "connection_type": "residential",
        "sanctioned_load": 5, "tariff_type": "Domestic", "connection_date": "2026-01-01"
    }
    r1 = client.post("/api/v1/connections", json=payload, headers=auth_headers)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/connections", json=payload, headers=auth_headers)
    assert r2.status_code == 409
