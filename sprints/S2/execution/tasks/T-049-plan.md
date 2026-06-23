# T-049 — AdjustmentService (F-009)

**Module:** M-002 · **Depends on:** T-043, T-045, T-046 · **DS:** DS-002, DS-007

## Implementation logic

```python
class AdjustmentService:
    def save_adjustment(self, payload: AdjustmentCreate) -> AdjustmentRead:
        # AC-035 already enforced at Pydantic layer (T-046 model_validator); defense-in-depth here:
        if payload.stock_date > payload.entry_date:
            raise ValidationError("stock_date must be on or before entry_date")

        # Assert design exists + active
        design = self.design_repo.get(payload.design_id)
        if not design.is_active:
            raise ValidationError(f"Design {payload.design_id} is inactive")

        # AC-040 — design must have ≥1 active (design, grade) mapping
        active_pairs = self.map_repo.list_active_by_design(payload.design_id)
        if not active_pairs:
            raise ValidationError(
                f"Design {payload.design_id} has no active grade combinations (ERR-012)"
            )
        active_grade_ids = {p.grade_id for p in active_pairs}

        # Each line's grade_id must be in active pairs for this design
        for line in payload.lines:
            if line.grade_id not in active_grade_ids:
                raise ValidationError(
                    f"Grade {line.grade_id} is not an active mapping for design {payload.design_id}"
                )

        # Snapshot software_cb per line via domain.stock.closing_balance(stock_date)
        # and compute difference = physical_cb - software_cb (AC-038)
        line_payloads = []
        line_diffs = []  # parallel list for ledger application
        for line in payload.lines:
            software_cb = stock.closing_balance(
                self.session, payload.design_id, line.grade_id, payload.stock_date,
            )
            difference = line.physical_cb - software_cb
            line_payloads.append({
                "grade_id": line.grade_id,
                "software_cb": software_cb,
                "physical_cb": line.physical_cb,
                "difference": difference,
            })
            line_diffs.append((line.grade_id, difference))

        # Persist header + lines
        header = self.repo.create_with_lines(
            header_payload={
                "stock_date": payload.stock_date,
                "entry_date": payload.entry_date,
                "design_id": payload.design_id,
                "entered_by_id": payload.entered_by_id,
            },
            line_payloads=line_payloads,
        )

        # Apply ledger writes (delta = difference; can be negative)
        # Use header.entry_date as txn_date — adjustments are dated at entry_date per LLD scope_notes.
        # Actually re-check: HLD/PRD specifies stock_date as the business date; ledger writes use stock_date.
        for (grade_id, difference), persisted_line in zip(line_diffs, header.lines):
            if difference != 0:  # zero-difference skipped (no ledger row needed)
                stock.apply_adjustment(
                    self.session, payload.design_id, grade_id,
                    payload.stock_date, difference,
                    header.header_id, persisted_line.line_id,
                )
            # If difference == 0, the persisted line row remains (audit trail) but no ledger movement.

        self.session.commit()
        return AdjustmentRead.model_validate(header)
```

## Constraints
- DS-002/DS-007: same as T-047.
- AC-034: ENFORCED at the Pydantic layer (T-046 — design_id is on header, not lines). Service doesn't need to re-check structure.
- AC-038: `difference = physical_cb - software_cb`. Can be negative — no `abs()`.
- AC-040 / ERR-012: surfaced as ValidationError; router→handler maps to 422.
- Note on txn_date: ledger uses `stock_date` (the business date), NOT entry_date — software_cb was computed AS OF stock_date.
- Optimization note: `difference == 0` skips the ledger row but keeps the adjustment_line row for audit. Acceptable per PRD; document if reviewer flags.

## Do not touch
Any other file.

## Success criteria
- **Manual:** Save adjustment; software_cb pulled from ledger; difference correct; ledger delta applied.
- **Automated:** TC-074, TC-075, TC-077 pass.
- **DoD:** All AC-034..AC-040 invariants enforced.

## Checkout prompt
*"AdjustmentService created; difference=physical-software; ledger applies delta=difference."*
