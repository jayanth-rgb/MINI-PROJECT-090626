# T-090 tests — routers/pricing.py (no dedicated TCs)

No direct router-level TCs. Service coverage via TC-201 (PricingService).

| Verified via | TC | What is asserted |
|---|---|---|
| T-083 PricingService | TC-201 | create_price validates FK, 409 on duplicate design+grade+effective_from |
| T-084 InvoiceService | TC-202..TC-206 | InvoiceService fetches active price — correct unit_price snapshotted on invoice line (DS-022) |

**Manual smoke test** (after implementation): POST /prices with SUPERVISOR auth + valid PriceMasterCreate payload → 201; GET /prices with any auth → 200 list.
