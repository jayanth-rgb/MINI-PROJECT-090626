"""Pydantic schema validation tests for the 6 master entities.

Covers: TC-002, TC-003, TC-009, TC-013, TC-021.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.schemas.master import (
    DealerCreate,
    DesignCreate,
    StaffCreate,
    SupplierCreate,
)


def _first_error(exc: ValidationError) -> dict:
    return exc.errors()[0]


def test_tc002_supplier_create_rejects_empty_supplier_name() -> None:
    with pytest.raises(ValidationError) as exc_info:
        SupplierCreate(supplier_name="", place="Mallur")

    err = _first_error(exc_info.value)
    assert err["loc"] == ("supplier_name",)
    assert err["type"] == "string_too_short"


def test_tc003_supplier_create_rejects_empty_place() -> None:
    with pytest.raises(ValidationError) as exc_info:
        SupplierCreate(supplier_name="Manjunatha", place="")

    err = _first_error(exc_info.value)
    assert err["loc"] == ("place",)
    assert err["type"] == "string_too_short"


def test_tc009_staff_create_rejects_empty_staff_name() -> None:
    with pytest.raises(ValidationError) as exc_info:
        StaffCreate(staff_name="")

    err = _first_error(exc_info.value)
    assert err["loc"] == ("staff_name",)
    assert err["type"] == "string_too_short"


@pytest.mark.parametrize(
    "dealer_name,place,expected_field",
    [
        ("", "Dindivanam", "dealer_name"),
        ("Raj", "", "place"),
    ],
)
def test_tc013_dealer_create_rejects_empty_fields(
    dealer_name: str, place: str, expected_field: str
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        DealerCreate(dealer_name=dealer_name, place=place)

    fields_with_errors = {e["loc"][0] for e in exc_info.value.errors()}
    assert expected_field in fields_with_errors


@pytest.mark.parametrize(
    "size,design_name,expected_field",
    [
        ("", "16X10 Ridges", "size"),
        ("16X10", "", "design_name"),
    ],
)
def test_tc021_design_create_rejects_empty_fields(
    size: str, design_name: str, expected_field: str
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        DesignCreate(size=size, design_name=design_name)

    fields_with_errors = {e["loc"][0] for e in exc_info.value.errors()}
    assert expected_field in fields_with_errors
