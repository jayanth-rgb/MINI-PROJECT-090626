# T-048 — SalesService (F-008)

**Module:** M-002 · **Depends on:** T-043, T-045, T-046 · **DS:** DS-002, DS-007, DS-013

## Implementation logic

Mirror of `InwardService.save_inward` with these substitutions:
- `purchase_date` → `sales_date`
- `supplier_id` → `dealer_id`, fetched from `DealerRepository`, snapshot `dealer.place` per DS-013
- `entered_by_id` → both `loading_staff_id` AND `verified_by_id` — BOTH required, BOTH must be active (AC-030)
- `stock.apply_inward` → `stock.apply_sale` (delta = -nos)
- AC-028 date bounds: `today - 7 ≤ sales_date ≤ today` (same as AC-020/021 logic)

```python
class SalesService:
    def __init__(self, session: Session): ...

    def save_sale(self, payload: SalesCreate) -> SalesRead:
        # AC-028 date validation
        # AC-029 dealer active + snapshot place
        dealer = self.dealer_repo.get(payload.dealer_id)
        # AC-030 both staff required + active — Pydantic enforces presence; service checks active
        for staff_id in (payload.loading_staff_id, payload.verified_by_id):
            staff = self.staff_repo.get(staff_id)
            if not staff.is_active:
                raise ValidationError(f"Staff {staff_id} is inactive")
        # AC-031/032 line stripping + active pair check (same as Inward)
        # ...
        header = self.repo.create_with_lines(
            header_payload={
                "sales_date": payload.sales_date,
                "dealer_id": payload.dealer_id,
                "place": dealer.place,
                "loading_staff_id": payload.loading_staff_id,
                "verified_by_id": payload.verified_by_id,
            },
            line_payloads=...,
        )
        for line in header.lines:
            stock.apply_sale(session, line.design_id, line.grade_id, payload.sales_date,
                             line.nos, header.header_id, line.line_id)
        self.session.commit()
        return SalesRead.model_validate(header)

    def list_sales(self, date_from=None, date_to=None, dealer_ids=None, design_ids=None) -> list[SalesRead]:
        # Filter via select() — S3's Sales Report will reuse this shape.
        ...
```

## Constraints
- DS-002/DS-007/DS-013: same as T-047.
- AC-030: BOTH `loading_staff_id` and `verified_by_id` required (Pydantic in T-046 enforces) AND active (service checks). DB has no rule that they must DIFFER; same staff is allowed if business chooses.

## Do not touch
Any other file.

## Success criteria
- **Manual:** Save a sale; balance decreases per line.
- **Automated:** TC-058, TC-059, TC-060, TC-062, TC-063, TC-065 all pass.
- **DoD:** All AC-028..AC-033 invariants enforced.

## Checkout prompt
*"SalesService created; ledger decreases per line via apply_sale."*
