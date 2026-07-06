"""ST-013 — POST /auth/login median round-trip < 500ms (V2 non_functional.performance).

Seeds one SUPERVISOR user, times 20 sequential login round-trips against
TestClient (in-process — dominant cost is bcrypt verify + JWT sign), and
asserts the median duration stays inside the PRD 500ms form-save budget.
"""
from __future__ import annotations

import statistics
import time

from src.domain.auth import get_password_hash
from src.infrastructure.db.models.auth import UserModel


def test_st013_auth_login_median_under_500ms(unauthenticated_client, db_session):
    db_session.add(
        UserModel(
            username="perf_user",
            password_hash=get_password_hash("perf-pass-13"),
            role="SUPERVISOR",
            is_active=True,
        )
    )
    db_session.flush()

    durations_ms: list[float] = []
    for _ in range(20):
        t0 = time.perf_counter()
        resp = unauthenticated_client.post(
            "/api/v1/auth/login",
            data={"username": "perf_user", "password": "perf-pass-13"},
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert resp.status_code == 200, f"login failed: {resp.text}"
        durations_ms.append(elapsed_ms)

    median = statistics.median(durations_ms)
    assert median < 500.0, (
        f"ST-013 median login latency {median:.1f}ms exceeds 500ms threshold; "
        f"samples={[round(d, 1) for d in durations_ms]}"
    )
    # Emit for report_capture — visible on -s
    print(f"\nST-013 median={median:.1f}ms n=20")
