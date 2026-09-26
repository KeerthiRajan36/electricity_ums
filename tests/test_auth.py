def test_customer_self_registration_and_login(client):
    r = client.post("/api/v1/auth/register", json={
        "full_name": "Jane Doe", "email": "jane@example.com", "password": "JanePass123"
    })
    assert r.status_code == 201
    assert r.json()["role"] == "customer"

    r = client.post("/api/v1/auth/login", json={"email": "jane@example.com", "password": "JanePass123"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and "refresh_token" in body


def test_login_with_wrong_password_fails(client):
    client.post("/api/v1/auth/register", json={
        "full_name": "Jane Doe", "email": "jane2@example.com", "password": "JanePass123"
    })
    r = client.post("/api/v1/auth/login", json={"email": "jane2@example.com", "password": "WrongPass"})
    assert r.status_code == 401


def test_self_registration_cannot_create_staff_role(client):
    r = client.post("/api/v1/auth/register", json={
        "full_name": "Wannabe Admin", "email": "wannabe@example.com",
        "password": "Pass12345", "role": "super_admin"
    })
    assert r.status_code == 403


def test_super_admin_can_create_staff_account(client, auth_headers):
    r = client.post("/api/v1/auth/register", json={
        "full_name": "Officer Bob", "email": "bob@utility.com",
        "password": "BobPass123", "role": "billing_officer"
    }, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["role"] == "billing_officer"


def test_me_and_change_password(client, auth_headers):
    r = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "admin@test.com"

    r = client.put("/api/v1/auth/change-password", json={
        "old_password": "Admin@12345", "new_password": "NewPass456"
    }, headers=auth_headers)
    assert r.status_code == 204

    # Old password should no longer work, new one should
    r = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Admin@12345"})
    assert r.status_code == 401
    r = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "NewPass456"})
    assert r.status_code == 200


def test_refresh_token_flow(client):
    client.post("/api/v1/auth/register", json={
        "full_name": "Refresh User", "email": "refresh@example.com", "password": "RefreshPass1"
    })
    login = client.post("/api/v1/auth/login", json={"email": "refresh@example.com", "password": "RefreshPass1"})
    refresh_token = login.json()["refresh_token"]

    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_protected_endpoint_requires_auth(client):
    r = client.get("/api/v1/customers")
    assert r.status_code == 401
