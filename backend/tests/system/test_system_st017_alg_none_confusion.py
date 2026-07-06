"""ST-017 — JWT alg=none confusion attack rejected (401).

An unsigned JWT with header alg=none must never be accepted. Verifies that
the decoder is not tricked into skipping signature verification even when the
attacker declares the token requires no signature.
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def test_st017_alg_none_returns_401(unauthenticated_client):
    header = _b64u(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    payload = _b64u(
        json.dumps({"sub": "attacker", "role": "SUPERVISOR", "exp": exp}).encode()
    )
    # Empty signature per RFC 7519 unsigned token
    forged = f"{header}.{payload}."

    resp = unauthenticated_client.get(
        "/api/v1/suppliers", headers={"Authorization": f"Bearer {forged}"}
    )
    assert resp.status_code == 401, (
        f"alg=none JWT was NOT rejected: {resp.status_code} {resp.text}"
    )
