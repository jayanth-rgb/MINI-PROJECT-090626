"""V2 TC-171..TC-175 — domain.auth (bcrypt hash/verify + JWT encode/decode).

Deterministic unit tests: hashes are re-generated per-test via get_password_hash
(bcrypt output is non-deterministic but verify_password is the invariant).
SECRET_KEY is set explicitly to keep the JWT encode/decode round-trip stable
across runs regardless of the host's environment.
"""
from __future__ import annotations

import os
from datetime import timedelta

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-v2-tests")

from src.domain.auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_tc171_verify_password_true_when_plain_matches_hash():
    hashed = get_password_hash("admin123")
    assert verify_password("admin123", hashed) is True


def test_tc172_verify_password_false_when_plain_does_not_match_hash():
    hashed = get_password_hash("admin123")
    assert verify_password("wrongpassword", hashed) is False


def test_tc173_create_access_token_encodes_sub_and_role_with_future_exp():
    token = create_access_token(
        data={"sub": "admin", "role": "SUPERVISOR"},
        expires_delta=timedelta(seconds=28800),
    )
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "admin"
    assert payload["role"] == "SUPERVISOR"
    # exp is a POSIX timestamp; must be in the future relative to iat implied by encode.
    from datetime import datetime, timezone
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()


def test_tc174_decode_access_token_returns_none_for_expired_token():
    expired = create_access_token(
        data={"sub": "admin"},
        expires_delta=timedelta(seconds=-1),
    )
    assert decode_access_token(expired) is None


def test_tc175_decode_access_token_returns_none_for_malformed_token():
    assert decode_access_token("not.a.valid.jwt.string") is None
