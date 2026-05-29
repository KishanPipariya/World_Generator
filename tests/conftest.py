from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(request: pytest.FixtureRequest) -> TestClient:
    test_client = TestClient(app, base_url="http://testserver/api/v1")
    username = f"testuser_{request.node.name}"
    username = "".join(char if char.isalnum() else "_" for char in username)[:80]
    password = "test-password"
    email = f"{username}@example.com"
    register = test_client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert register.status_code in {201, 409}, register.json()
    login = test_client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert login.status_code == 200, login.json()
    token = login.json()["access_token"]
    test_client.headers.update({"Authorization": f"Bearer {token}"})
    return test_client
