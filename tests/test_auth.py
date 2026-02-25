"""Tests for /api/v1/auth endpoints"""
import pytest
from fastapi.testclient import TestClient


# ── Registration ───────────────────────────────────────────────────────────────

def test_register_success(client: TestClient):
    resp = client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "password": "securepass123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "user_id" in body
    assert body["expires_in"] > 0


def test_register_duplicate_username(client: TestClient):
    payload = {"username": "dupeuser", "password": "password123"}
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409
    assert "already taken" in r2.json()["detail"]


def test_register_password_too_short(client: TestClient):
    resp = client.post(
        "/api/v1/auth/register",
        json={"username": "shortpass", "password": "abc"},
    )
    assert resp.status_code == 422


def test_register_username_too_short(client: TestClient):
    resp = client.post(
        "/api/v1/auth/register",
        json={"username": "ab", "password": "validpassword"},
    )
    assert resp.status_code == 422


# ── Login ──────────────────────────────────────────────────────────────────────

def test_login_success(client: TestClient):
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={"username": "loginuser", "password": "mypassword1"},
    )

    # Login via OAuth2 form
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "loginuser", "password": "mypassword1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"username": "wrongpass_user", "password": "correctpass1"},
    )

    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "wrongpass_user", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert "Incorrect" in resp.json()["detail"]


def test_login_unknown_user(client: TestClient):
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "nobody", "password": "whatever"},
    )
    assert resp.status_code == 401


# ── Token usage ────────────────────────────────────────────────────────────────

def test_token_grants_access_to_protected_route(client: TestClient):
    """A token obtained from /auth/register should authenticate to bookmark endpoints."""
    reg = client.post(
        "/api/v1/auth/register",
        json={"username": "tokenuser", "password": "tokenpass1"},
    )
    token = reg.json()["access_token"]

    resp = client.get(
        "/api/v1/bookmarks",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_invalid_token_rejected(client: TestClient):
    resp = client.get(
        "/api/v1/bookmarks",
        headers={"Authorization": "Bearer this.is.not.valid"},
    )
    assert resp.status_code == 401


def test_no_auth_rejected(client: TestClient):
    resp = client.get("/api/v1/bookmarks")
    assert resp.status_code == 401
