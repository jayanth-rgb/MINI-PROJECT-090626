"""TC-150, TC-151, TC-152 — DesignGradeMapRepository.list_active_all (F-010, M-001).

Tests the new S3 method: returns all active (map.is_active=True AND grade.is_active=True)
pairs across ALL designs. Edge cases test that deactivated maps and deactivated grades
are correctly excluded. Co-located per project convention.
"""
from __future__ import annotations

from src.infrastructure.db.models.master import (
    DesignGradeMapModel,
    GradeModel,
    TradingDesignModel,
)
from src.infrastructure.db.repositories.master import DesignGradeMapRepository


# ---------------------------------------------------------------------------
# In-file seed helpers
# ---------------------------------------------------------------------------


def _seed_design(db, name="Test Design", size="16X10"):
    d = TradingDesignModel(design_name=name, size=size, is_active=True)
    db.add(d)
    db.flush()
    return d


def _seed_grade(db, code, is_active=True):
    g = GradeModel(grade_code=code, is_active=is_active)
    db.add(g)
    db.flush()
    return g


def _seed_map(db, design_id, grade_id, is_active=True):
    m = DesignGradeMapModel(design_id=design_id, grade_id=grade_id, is_active=is_active)
    db.add(m)
    db.flush()
    return m


# ---------------------------------------------------------------------------
# TC-150 — All active maps across all designs returned
# ---------------------------------------------------------------------------


def test_tc150_list_active_all_returns_all_active_maps(db_session):
    """TC-150: list_active_all returns all rows where map.is_active AND grade.is_active."""
    d1 = _seed_design(db_session, "16X10 Ridges", "16X10")
    d2 = _seed_design(db_session, "12X8 Ridges", "12X8")
    d3 = _seed_design(db_session, "11X7 Ridges", "11X7")

    g1 = _seed_grade(db_session, "1")
    g2 = _seed_grade(db_session, "2")

    m1 = _seed_map(db_session, d1.design_id, g1.grade_id)
    m2 = _seed_map(db_session, d1.design_id, g2.grade_id)
    m3 = _seed_map(db_session, d2.design_id, g1.grade_id)
    m4 = _seed_map(db_session, d3.design_id, g2.grade_id)
    db_session.flush()

    repo = DesignGradeMapRepository(db_session)
    result = repo.list_active_all()

    returned_map_ids = sorted([r.map_id for r in result])
    expected_map_ids = sorted([m1.map_id, m2.map_id, m3.map_id, m4.map_id])
    assert len(result) == 4
    assert returned_map_ids == expected_map_ids

    # Verify eager-loaded relationships are accessible (no N+1)
    for r in result:
        assert r.design is not None
        assert r.grade is not None


# ---------------------------------------------------------------------------
# TC-151 — Edge: map.is_active=False excluded (S1 AC-017 soft-delete preserved)
# ---------------------------------------------------------------------------


def test_tc151_inactive_map_excluded(db_session):
    """TC-151: map.is_active=False must be excluded (soft-delete contract AC-017)."""
    d = _seed_design(db_session, "16X10 Ridges", "16X10")
    g1 = _seed_grade(db_session, "1")
    g2 = _seed_grade(db_session, "2")

    m1 = _seed_map(db_session, d.design_id, g1.grade_id, is_active=True)
    # Deactivated map — should NOT appear
    _seed_map(db_session, d.design_id, g2.grade_id, is_active=False)
    db_session.flush()

    repo = DesignGradeMapRepository(db_session)
    result = repo.list_active_all()

    assert len(result) == 1
    assert result[0].map_id == m1.map_id


# ---------------------------------------------------------------------------
# TC-152 — Edge: inactive grade excluded via transitive JOIN filter (AC-012)
# ---------------------------------------------------------------------------


def test_tc152_inactive_grade_excluded_via_join(db_session):
    """TC-152: grade.is_active=False must cascade to exclude the map (AC-012)."""
    d = _seed_design(db_session, "16X10 Ridges", "16X10")
    g1 = _seed_grade(db_session, "1", is_active=True)
    # Grade soft-deleted by admin
    g2 = _seed_grade(db_session, "2", is_active=False)

    m1 = _seed_map(db_session, d.design_id, g1.grade_id, is_active=True)
    # Map is_active=True but grade is inactive — should be excluded
    _seed_map(db_session, d.design_id, g2.grade_id, is_active=True)
    db_session.flush()

    repo = DesignGradeMapRepository(db_session)
    result = repo.list_active_all()

    assert len(result) == 1
    assert result[0].map_id == m1.map_id
