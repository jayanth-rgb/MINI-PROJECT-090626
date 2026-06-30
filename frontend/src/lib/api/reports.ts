// S3 — Integration boundary for the sales report endpoint (T-065).
//
// Integrated against the real FastAPI backend at GET /api/v1/reports/sales.
//
// CRITICAL: FastAPI list params require repeat-key serialization
// (?dealer_ids=1&dealer_ids=2), NOT comma-joined (?dealer_ids=1,2).
// URLSearchParams.append() emits the correct repeat-key shape; axios passes
// URLSearchParams instances through verbatim.

import type {
  SalesReportFilters,
  SalesReportResponse,
} from "@/types/reports";
import { apiClient } from "@/lib/api/client";

/**
 * Fetch the sales report applying the given filters.
 *
 * All filters optional and multi-select per RULE-018; no filters returns the
 * full dataset. Server returns { consolidation, transactions } with:
 *   - consolidation grouped by (design_id, grade_id) sorted by
 *     (design_name ASC, grade_code ASC) — RULE-019
 *   - transactions sorted by (sales_date ASC, header_id ASC) — RULE-020
 * Server asserts AC-050: sum(transactions.nos) == sum(consolidation.total_nos);
 * a violation surfaces as HTTP 500 (defense-in-depth — DS-017 shared filter
 * predicate makes the violation structurally impossible by construction).
 */
export async function getSalesReport(
  filters: SalesReportFilters
): Promise<SalesReportResponse> {
  const params = new URLSearchParams();
  if (filters.dateFrom) params.append("date_from", filters.dateFrom);
  if (filters.dateTo) params.append("date_to", filters.dateTo);
  filters.dealerIds?.forEach((id) => params.append("dealer_ids", String(id)));
  filters.places?.forEach((p) => params.append("places", p));
  filters.designIds?.forEach((id) => params.append("design_ids", String(id)));

  const response = await apiClient.get<SalesReportResponse>("/reports/sales", {
    params,
  });
  return response.data;
}
