def _setup_connection(client, headers, suffix):
    customer = client.post("/api/v1/customers", json={
        "customer_number": f"CUST-B{suffix}", "full_name": "Billing Test", "email": f"billtest{suffix}@example.com",
        "phone": "9000000001", "address": "2 Main St", "city": "Chennai"
    }, headers=headers).json()

    connection = client.post("/api/v1/connections", json={
        "customer_id": customer["id"], "connection_number": f"CONN-B{suffix}", "connection_type": "residential",
        "sanctioned_load": 5, "tariff_type": "Domestic", "connection_date": "2026-01-01"
    }, headers=headers).json()

    return customer, connection


def _setup_tariff(client, headers):
    for name, mn, mx, rate in [
        ("Domestic-Slab1", 0, 100, 3.5), ("Domestic-Slab2", 100, 200, 4.5), ("Domestic-Slab3", 200, None, 6.0)
    ]:
        payload = {
            "tariff_name": name, "connection_type": "residential", "minimum_units": mn,
            "rate_per_unit": rate, "fixed_charge": 50, "effective_from": "2026-01-01",
        }
        if mx is not None:
            payload["maximum_units"] = mx
        r = client.post("/api/v1/tariffs", json=payload, headers=headers)
        assert r.status_code == 201


def test_full_billing_and_payment_flow(client, auth_headers):
    customer, connection = _setup_connection(client, auth_headers, "01")
    _setup_tariff(client, auth_headers)

    meter = client.post("/api/v1/meters", json={
        "connection_id": connection["id"], "meter_number": "MTR-B01", "meter_type": "smart",
        "installation_date": "2026-01-01", "initial_reading": 0
    }, headers=auth_headers).json()

    # 250 units -> spans all three slabs: 100*3.5 + 100*4.5 + 50*6.0 = 1100 energy, +50 fixed, +5% tax
    r = client.post("/api/v1/meter-readings", json={
        "meter_id": meter["id"], "reading_date": "2026-01-31", "current_reading": 250,
        "reading_source": "smart_meter"
    }, headers=auth_headers)
    assert r.status_code == 201
    assert float(r.json()["units_consumed"]) == 250.0

    r = client.post("/api/v1/bills/generate", json={
        "connection_id": connection["id"], "billing_month": "2026-01"
    }, headers=auth_headers)
    assert r.status_code == 201
    bill = r.json()
    assert float(bill["energy_charge"]) == 1100.0
    assert float(bill["fixed_charge"]) == 50.0
    assert float(bill["tax"]) == 57.5
    assert float(bill["total_amount"]) == 1207.5

    # Duplicate bill for same connection+month rejected
    r = client.post("/api/v1/bills/generate", json={
        "connection_id": connection["id"], "billing_month": "2026-01"
    }, headers=auth_headers)
    assert r.status_code == 409

    # Overpayment rejected
    r = client.post(f"/api/v1/payments/{bill['id']}", json={
        "amount": 99999, "payment_method": "upi", "transaction_id": f"TXN-OVER-{bill['id']}"
    }, headers=auth_headers)
    assert r.status_code == 400

    # Correct payment succeeds and marks bill paid
    r = client.post(f"/api/v1/payments/{bill['id']}", json={
        "amount": bill["total_amount"], "payment_method": "upi", "transaction_id": f"TXN-OK-{bill['id']}"
    }, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["payment_status"] == "success"

    r = client.get(f"/api/v1/bills/{bill['id']}", headers=auth_headers)
    assert r.json()["bill_status"] == "paid"

    # A transaction_id already used (even against a different, still-unpaid
    # bill) must be rejected as a duplicate.
    r = client.post("/api/v1/meter-readings", json={
        "meter_id": meter["id"], "reading_date": "2026-02-28", "current_reading": 300,
        "reading_source": "smart_meter"
    }, headers=auth_headers)
    assert r.status_code == 201

    bill2 = client.post("/api/v1/bills/generate", json={
        "connection_id": connection["id"], "billing_month": "2026-02"
    }, headers=auth_headers).json()

    r = client.post(f"/api/v1/payments/{bill2['id']}", json={
        "amount": 1, "payment_method": "card", "transaction_id": f"TXN-OK-{bill['id']}"
    }, headers=auth_headers)
    assert r.status_code == 409


def test_duplicate_reading_same_period_rejected(client, auth_headers):
    customer, connection = _setup_connection(client, auth_headers, "02")
    meter = client.post("/api/v1/meters", json={
        "connection_id": connection["id"], "meter_number": "MTR-B02", "meter_type": "smart",
        "installation_date": "2026-01-01", "initial_reading": 0
    }, headers=auth_headers).json()

    r1 = client.post("/api/v1/meter-readings", json={
        "meter_id": meter["id"], "reading_date": "2026-02-15", "current_reading": 50
    }, headers=auth_headers)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/meter-readings", json={
        "meter_id": meter["id"], "reading_date": "2026-02-20", "current_reading": 80
    }, headers=auth_headers)
    assert r2.status_code == 409  # same billing_period (2026-02)


def test_reading_cannot_go_backwards(client, auth_headers):
    customer, connection = _setup_connection(client, auth_headers, "03")
    meter = client.post("/api/v1/meters", json={
        "connection_id": connection["id"], "meter_number": "MTR-B03", "meter_type": "smart",
        "installation_date": "2026-01-01", "initial_reading": 100
    }, headers=auth_headers).json()

    r = client.post("/api/v1/meter-readings", json={
        "meter_id": meter["id"], "reading_date": "2026-03-01", "current_reading": 50
    }, headers=auth_headers)
    assert r.status_code == 400
