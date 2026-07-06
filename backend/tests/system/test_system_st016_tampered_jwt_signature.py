"""ST-016 — JWT signed with foreign SECRET_KEY rejected (401).

Verifies HS256 signature is actually verified server-side. Mitigates RI-V2-001
(SECRET_KEY handling) by proving that a token signed with a leaked or wrong
key is not accepted just because the payload structure is correct.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt


def test_st016_foreign_signed_jwt_returns_401(unauthenticated_client):
    payload = {
        "sub": "attacker",
        "role": "SUPERVISOR",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    forged = jwt.encode(payload, "ATTACKER-DIFFERENT-KEY", algorithm="HS256")
    resp = unauthenticated_client.get(
        "/api/v1/suppliers", headers={"Authorization": f"Bearer {forged}"}
    )
    assert resp.status_code == 401, (
        f"foreign-signed JWT was NOT rejected: {resp.status_code} {resp.text}"
    )
