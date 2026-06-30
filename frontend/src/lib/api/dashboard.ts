// S3 — Integration boundary for the dashboard endpoint (T-064).
//
// Integrated against the real FastAPI backend at GET /api/v1/dashboard.
// Every component/hook imports getDashboard from this module only.

import type { DashboardRow } from "@/types/dashboard";
import { apiClient } from "@/lib/api/client";

/**
 * Fetch the stock dashboard for the given as-of date.
 *
 * Server returns list[DashboardRow] sorted by (design_name ASC, grade_code ASC).
 * Server asserts FORMULA-001 invariant per row (opening + inward − outward + adjust == closing);
 * a violation surfaces as HTTP 500 (DS-016 ledger-corruption signal).
 */
export async function getDashboard(asOfDate: string): Promise<DashboardRow[]> {
  const response = await apiClient.get<DashboardRow[]>("/dashboard", {
    params: { as_of_date: asOfDate },
  });
  return response.data;
}
