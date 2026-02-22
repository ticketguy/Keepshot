"""Tests for /api/v1/notifications endpoints"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.models.notification import Notification, NotificationType


_FAKE_BOOKMARK_ID = "00000000-0000-0000-0000-000000000001"


def _make_notification(db, user_id: str, read: bool = False) -> Notification:
    """Helper to insert a notification directly into the test DB.

    Uses a fake bookmark_id UUID — SQLite does not enforce FK references.
    """
    n = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        bookmark_id=_FAKE_BOOKMARK_ID,
        change_id=None,
        notification_type=NotificationType.CHANGE,
        title="Price dropped",
        message="The item is now $10 cheaper.",
        read=read,
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


# ── Auth guard ─────────────────────────────────────────────────────────────────

def test_list_notifications_requires_auth(client: TestClient):
    assert client.get("/api/v1/notifications").status_code == 401


# ── List ───────────────────────────────────────────────────────────────────────

def test_list_notifications_empty(client: TestClient, auth_headers, test_user):
    resp = client.get("/api/v1/notifications", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []


def test_list_notifications_returns_items(client: TestClient, auth_headers, test_user, db):
    _make_notification(db, test_user.id)
    _make_notification(db, test_user.id, read=True)

    resp = client.get("/api/v1/notifications", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_list_notifications_filter_by_read(client: TestClient, auth_headers, test_user, db):
    _make_notification(db, test_user.id, read=False)
    _make_notification(db, test_user.id, read=True)

    unread = client.get("/api/v1/notifications?read=false", headers=auth_headers)
    read = client.get("/api/v1/notifications?read=true", headers=auth_headers)

    assert unread.json()["total"] == 1
    assert read.json()["total"] == 1


# ── Get single ─────────────────────────────────────────────────────────────────

def test_get_notification(client: TestClient, auth_headers, test_user, db):
    n = _make_notification(db, test_user.id)
    resp = client.get(f"/api/v1/notifications/{n.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == n.id


def test_get_nonexistent_notification(client: TestClient, auth_headers):
    resp = client.get("/api/v1/notifications/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


# ── Mark read ──────────────────────────────────────────────────────────────────

def test_mark_notification_read(client: TestClient, auth_headers, test_user, db):
    n = _make_notification(db, test_user.id, read=False)

    resp = client.patch(
        f"/api/v1/notifications/{n.id}",
        json={"read": True},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["read"] is True


def test_mark_all_read(client: TestClient, auth_headers, test_user, db):
    _make_notification(db, test_user.id, read=False)
    _make_notification(db, test_user.id, read=False)

    resp = client.post("/api/v1/notifications/mark-all-read", headers=auth_headers)
    assert resp.status_code == 200
    assert "2" in resp.json()["message"]

    unread = client.get("/api/v1/notifications?read=false", headers=auth_headers)
    assert unread.json()["total"] == 0


# ── Delete ─────────────────────────────────────────────────────────────────────

def test_delete_notification(client: TestClient, auth_headers, test_user, db):
    n = _make_notification(db, test_user.id)

    del_resp = client.delete(f"/api/v1/notifications/{n.id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/notifications/{n.id}", headers=auth_headers)
    assert get_resp.status_code == 404


# ── Isolation ──────────────────────────────────────────────────────────────────

def test_cannot_read_other_users_notification(client: TestClient, auth_headers, db):
    from app.models.user import User
    from app.dependencies import create_access_token

    other = User(id="notif-other-uuid", username="notifother")
    db.add(other)
    db.commit()

    n = _make_notification(db, other.id)

    # test_user tries to access other user's notification
    resp = client.get(f"/api/v1/notifications/{n.id}", headers=auth_headers)
    assert resp.status_code == 404
