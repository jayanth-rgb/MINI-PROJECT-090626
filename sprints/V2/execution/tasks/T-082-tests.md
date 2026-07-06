# T-082 tests — none direct

`test_required=false` per LLD. Schema correctness verified transitively:

| Where | TCs | What is asserted |
|---|---|---|
| T-083 (PricingService) | TC-201 | PricingService.create_price returns PriceMasterRead; 409 duplicate raises correctly. |
| T-084 (InvoiceService) | TC-202..TC-206 | InvoiceService methods return InvoiceRead with total_amount, status, lines_count; PaymentCreate validated. |
| T-091 (invoices router) | TC-217 | POST /invoices response validates as InvoiceRead body. |

See [test_cases.json](../../design/test_cases.json) for full inputs/expected_output.
