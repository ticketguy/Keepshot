"""Tests for /api/v1/bookmarks endpoints"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# Fake scrape result for TEXT content (no network call needed)
TEXT_SCRAPE_RESULT = {
    "content": "Some test content here",
    "content_hash": "abc123",
    "file_path": None,
    "metadata": {"length": 22, "word_count": 4},
}

FAKE_WATCHPOINTS = [
    {
        "field_name": "content",
        "field_value": "Some test content here",
        "field_type": "text",
        "is_primary": True,
    }
]


# ── Auth guard ─────────────────────────────────────────────────────────────────

def test_create_bookmark_requires_auth(client: TestClient):
    resp = client.post("/api/v1/bookmarks", json={
        "content_type": "text",
        "title": "No auth",
        "raw_content": "content",
        "monitoring_enabled": False,
    })
    assert resp.status_code == 401


def test_list_bookmarks_requires_auth(client: TestClient):
    assert client.get("/api/v1/bookmarks").status_code == 401


# ── CRUD ───────────────────────────────────────────────────────────────────────

@patch("app.routers.bookmarks.ai_service.extract_watchpoints", new_callable=AsyncMock)
@patch("app.routers.bookmarks.monitor_bookmark", new_callable=AsyncMock)
def test_create_text_bookmark(mock_monitor, mock_wp, client: TestClient, auth_headers, test_user):
    mock_wp.return_value = FAKE_WATCHPOINTS

    resp = client.post(
        "/api/v1/bookmarks",
        json={
            "content_type": "text",
            "title": "My Note",
            "raw_content": "Some test content here",
            "monitoring_enabled": False,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "My Note"
    assert body["content_type"] == "text"
    assert body["user_id"] == test_user.id
    mock_wp.assert_called_once()


@patch("app.routers.bookmarks.ai_service.extract_watchpoints", new_callable=AsyncMock)
@patch("app.routers.bookmarks.monitor_bookmark", new_callable=AsyncMock)
def test_list_bookmarks_returns_created(mock_monitor, mock_wp, client: TestClient, auth_headers, test_user):
    mock_wp.return_value = FAKE_WATCHPOINTS

    # Create two bookmarks
    for i in range(2):
        client.post(
            "/api/v1/bookmarks",
            json={
                "content_type": "text",
                "title": f"Note {i}",
                "raw_content": f"Content {i}",
                "monitoring_enabled": False,
            },
            headers=auth_headers,
        )

    resp = client.get("/api/v1/bookmarks", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 2
    assert isinstance(body["items"], list)


@patch("app.routers.bookmarks.ai_service.extract_watchpoints", new_callable=AsyncMock)
@patch("app.routers.bookmarks.monitor_bookmark", new_callable=AsyncMock)
def test_get_bookmark_by_id(mock_monitor, mock_wp, client: TestClient, auth_headers, test_user):
    mock_wp.return_value = FAKE_WATCHPOINTS

    create_resp = client.post(
        "/api/v1/bookmarks",
        json={
            "content_type": "text",
            "title": "Fetch me",
            "raw_content": "hello",
            "monitoring_enabled": False,
        },
        headers=auth_headers,
    )
    bookmark_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/v1/bookmarks/{bookmark_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == bookmark_id


def test_get_nonexistent_bookmark(client: TestClient, auth_headers):
    resp = client.get("/api/v1/bookmarks/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


@patch("app.routers.bookmarks.ai_service.extract_watchpoints", new_callable=AsyncMock)
@patch("app.routers.bookmarks.monitor_bookmark", new_callable=AsyncMock)
def test_update_bookmark(mock_monitor, mock_wp, client: TestClient, auth_headers, test_user):
    mock_wp.return_value = FAKE_WATCHPOINTS

    create_resp = client.post(
        "/api/v1/bookmarks",
        json={
            "content_type": "text",
            "title": "Old title",
            "raw_content": "content",
            "monitoring_enabled": False,
        },
        headers=auth_headers,
    )
    bookmark_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/bookmarks/{bookmark_id}",
        json={"title": "New title"},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "New title"


@patch("app.routers.bookmarks.ai_service.extract_watchpoints", new_callable=AsyncMock)
@patch("app.routers.bookmarks.monitor_bookmark", new_callable=AsyncMock)
def test_delete_bookmark(mock_monitor, mock_wp, client: TestClient, auth_headers, test_user):
    mock_wp.return_value = FAKE_WATCHPOINTS

    create_resp = client.post(
        "/api/v1/bookmarks",
        json={
            "content_type": "text",
            "title": "Delete me",
            "raw_content": "content",
            "monitoring_enabled": False,
        },
        headers=auth_headers,
    )
    bookmark_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/bookmarks/{bookmark_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # Confirm gone
    get_resp = client.get(f"/api/v1/bookmarks/{bookmark_id}", headers=auth_headers)
    assert get_resp.status_code == 404


# ── Isolation ──────────────────────────────────────────────────────────────────

@patch("app.routers.bookmarks.ai_service.extract_watchpoints", new_callable=AsyncMock)
@patch("app.routers.bookmarks.monitor_bookmark", new_callable=AsyncMock)
def test_cannot_access_other_users_bookmark(mock_monitor, mock_wp, client: TestClient, auth_headers, test_user, db):
    """A second user should not be able to read the first user's bookmark."""
    from app.models.user import User
    from app.dependencies import create_access_token

    mock_wp.return_value = FAKE_WATCHPOINTS

    # Create bookmark as test_user
    create_resp = client.post(
        "/api/v1/bookmarks",
        json={"content_type": "text", "title": "Private", "raw_content": "secret", "monitoring_enabled": False},
        headers=auth_headers,
    )
    bookmark_id = create_resp.json()["id"]

    # Create second user and token
    other_user = User(id="other-user-uuid", username="otheruser", password_hash="x")
    db.add(other_user)
    db.commit()
    other_token = create_access_token(other_user.id)

    resp = client.get(
        f"/api/v1/bookmarks/{bookmark_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 404


# ── Pagination ─────────────────────────────────────────────────────────────────

def test_list_bookmarks_pagination_params(client: TestClient, auth_headers):
    resp = client.get("/api/v1/bookmarks?page=1&page_size=5", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["page_size"] == 5
