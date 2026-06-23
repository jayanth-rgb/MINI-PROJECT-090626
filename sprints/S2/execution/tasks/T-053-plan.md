# T-053 — Sales router

**Module:** M-002 · **Depends on:** T-051 · **DS:** DS-007, DS-010

## Implementation logic

Mirror of T-052 (Inward router) with:
- `prefix='/sales'`, `tags=['sales']`
- `SalesCreate` / `SalesRead` from `transactions.py`
- `service: SalesService = Depends(get_sales_service)`
- list endpoint accepts `dealer_ids: list[int] | None = Query(default=None)` and `design_ids: list[int] | None = Query(default=None)` (FastAPI handles `?dealer_ids=1&dealer_ids=2` natively)

```python
@router.get("", response_model=list[SalesRead])
def list_sales(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    dealer_ids: list[int] | None = Query(default=None),
    design_ids: list[int] | None = Query(default=None),
    service: SalesService = Depends(get_sales_service),
):
    return service.list_sales(
        date_from=date_from, date_to=date_to,
        dealer_ids=dealer_ids, design_ids=design_ids,
    )
```

## Constraints
- DS-007: pure delegation.
- The filter query params are scoped to admin reads + S3 Sales Report; do NOT prefilter or transform — pass through to service.

## Do not touch
Any other file.

## Success criteria
- **Manual:** OpenAPI exposes 2 endpoints.
- **Automated:** TC-066 passes.
- **DoD:** Multi-select filters work natively (FastAPI default).

## Checkout prompt
*"Sales router — POST + GET on /api/v1/sales with multi-select filters."*
