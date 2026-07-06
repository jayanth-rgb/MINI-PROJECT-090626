"""V2 TC-185, TC-186, TC-190..TC-194 — UserRepository + AuthService integration."""
from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-v2-tests")

import pytest
from fastapi import HTTPException

from src.application.services.auth_service import AuthService
from src.infrastructure.db.repositories.auth import UserRepository
from src.presentation.schemas.auth import UserCreate

from tests.integration.v2._helpers import make_token, seed_user


def test_tc185_get_by_username_returns_user_when_present(db_session):
    seed_user(db_session, "teststaff", role="STAFF", password="pass1234")
    row = UserRepository(db_session).get_by_username("teststaff")
    assert row is not None
    assert row.username == "teststaff"
    assert row.role == "STAFF"
    assert row.is_active is True


def test_tc186_get_by_username_returns_none_when_missing(db_session):
    row = UserRepository(db_session).get_by_username("nonexistent_user_xyz_abc")
    assert row is None


def test_tc190_authenticate_returns_token_response_for_valid_credentials(db_session):
    seed_user(db_session, "admin", role="SUPERVISOR", password="admin123")
    svc = AuthService(db_session)
    resp = svc.authenticate("admin", "admin123")
    assert resp.token_type == "bearer"
    assert resp.role == "SUPERVISOR"
    assert resp.access_token != ""


def test_tc191_authenticate_raises_401_when_password_wrong(db_session):
    seed_user(db_session, "admin", role="STAFF", password="admin123")
    svc = AuthService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        svc.authenticate("admin", "wrongpassword")
    assert exc_info.value.status_code == 401


def test_tc192_authenticate_raises_401_when_user_inactive(db_session):
    seed_user(db_session, "inactiveuser", role="STAFF", is_active=False, password="pass123")
    svc = AuthService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        svc.authenticate("inactiveuser", "pass123")
    assert exc_info.value.status_code == 401


def test_tc193_get_current_user_returns_user_for_valid_jwt(db_session):
    seed_user(db_session, "admin", role="SUPERVISOR", password="admin123")
    token = make_token("admin", "SUPERVISOR")
    svc = AuthService(db_session)
    user = svc.get_current_user(token)
    assert user.username == "admin"
    assert user.role == "SUPERVISOR"
    assert user.is_active is True


def test_tc194_create_user_raises_409_when_username_duplicate(db_session):
    seed_user(db_session, "dupuser", role="STAFF", password="original1")
    svc = AuthService(db_session)
    payload = UserCreate(username="dupuser", password="newpass123", role="VERIFIER")
    with pytest.raises(HTTPException) as exc_info:
        svc.create_user(payload)
    assert exc_info.value.status_code == 409
