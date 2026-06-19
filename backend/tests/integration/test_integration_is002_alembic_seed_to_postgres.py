"""IS-002 — DF-007 end-to-end: alembic migration 0002 + seed against a real PG.

Brings up a dedicated PostgreSQL testcontainer (not the conftest's shared one,
because that container is initialized via Base.metadata.create_all). Applies
the alembic migration programmatically against the new container, then runs
scripts.seed_master_data.main() against the same DB and asserts the 33-row
PRD-sample state — plus idempotency on re-run.

Closes the W5 verification gap for TD-005 and TD-006: this is the only S1
test that proves the hand-authored migration applies cleanly and that the
seed script integrates with the migrated schema.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

# Direct imports — the seed script module is the SUT under test.
from scripts import seed_master_data
from src.infrastructure.db.models.master import (
    DealerModel,
    DesignGradeMapModel,
    GradeModel,
    StaffModel,
    SupplierModel,
    TradingDesignModel,
)

BACKEND_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"


@pytest.fixture()
def alembic_pg(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[str, sessionmaker]]:
    """Dedicated testcontainer with the alembic migration applied (not create_all).

    env.py reads the URL from ``get_settings().database_url`` (see db/migrations/
    env.py:19), so we must seed DATABASE_URL and clear the get_settings cache
    *before* invoking ``command.upgrade``. Setting ``sqlalchemy.url`` on the
    Config object alone is not sufficient — env.py overrides it.
    """
    from src.config import get_settings

    with PostgresContainer("postgres:16") as pg:
        url = pg.get_connection_url().replace(
            "postgresql+psycopg2://", "postgresql+psycopg://"
        )
        monkeypatch.setenv("DATABASE_URL", url)
        get_settings.cache_clear()

        cfg = Config(str(ALEMBIC_INI))
        cfg.set_main_option("script_location", str(BACKEND_DIR / "db" / "migrations"))
        command.upgrade(cfg, "head")

        engine = create_engine(url, future=True)
        SessionMaker = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        try:
            yield url, SessionMaker
        finally:
            engine.dispose()
            get_settings.cache_clear()


def _count_all(session) -> dict[str, int]:
    return {
        "tbl_supplier_master": session.execute(
            select(func.count(SupplierModel.supplier_id))
        ).scalar_one(),
        "tbl_staff_master": session.execute(
            select(func.count(StaffModel.staff_id))
        ).scalar_one(),
        "tbl_dealer_master": session.execute(
            select(func.count(DealerModel.dealer_id))
        ).scalar_one(),
        "tbl_grade_master": session.execute(
            select(func.count(GradeModel.grade_id))
        ).scalar_one(),
        "tbl_trading_design_master": session.execute(
            select(func.count(TradingDesignModel.design_id))
        ).scalar_one(),
        "tbl_design_grade_map": session.execute(
            select(func.count(DesignGradeMapModel.map_id))
        ).scalar_one(),
    }


def test_is002(
    alembic_pg: tuple[str, sessionmaker], monkeypatch: pytest.MonkeyPatch
) -> None:
    url, SessionMakerForContainer = alembic_pg

    # Verify both UNIQUE constraints exist by name after the migration.
    with SessionMakerForContainer() as s:
        constraint_names = set(
            row[0]
            for row in s.execute(
                text(
                    """SELECT constraint_name FROM information_schema.table_constraints
                       WHERE constraint_type='UNIQUE'"""
                )
            ).all()
        )
    assert "uq_grade_master_grade_code" in constraint_names
    assert "uq_design_grade_map_design_grade" in constraint_names

    # Point the seed module at the alembic-migrated container.
    monkeypatch.setattr(seed_master_data, "SessionLocal", SessionMakerForContainer)

    # First run — inserts 33 rows.
    seed_master_data.main()
    with SessionMakerForContainer() as s:
        counts = _count_all(s)
    assert counts == {
        "tbl_supplier_master": 3,
        "tbl_staff_master": 9,
        "tbl_dealer_master": 3,
        "tbl_grade_master": 9,
        "tbl_trading_design_master": 3,
        "tbl_design_grade_map": 6,
    }
    assert sum(counts.values()) == 33

    # Re-run — must be idempotent, 0 new rows.
    seed_master_data.main()
    with SessionMakerForContainer() as s:
        counts_after = _count_all(s)
    assert counts_after == counts
