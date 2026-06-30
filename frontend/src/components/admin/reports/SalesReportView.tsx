"use client";

// S3 — Sales report container component (F-011).
// Owns 5-filter state (URL-synced per UR-S3-004).
// AC-049: Consolidation FIRST, then Transactions — one scroll, no tabs/toggle.
// UR-S3-003: ONE ReconciliationBadge, rendered near filter bar.
// UR-S3-001: uses Dealer and Design (frontend type names).
// UR-S3-002: derives places from loaded dealers (.place), deduped client-side.
// UR-S3-004: drops empty params before router.replace.

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

import { getSalesReport } from "@/lib/api/reports";
import { dealersApi, designsApi } from "@/lib/api/masters";
import { SalesReportFilterBar } from "./SalesReportFilterBar";
import { ConsolidationTable } from "./ConsolidationTable";
import { TransactionsTable } from "./TransactionsTable";
import { ReconciliationBadge } from "./ReconciliationBadge";
import { EmptyReportState } from "./EmptyReportState";
import type { SalesReportFilters } from "@/types/reports";
import type { ApiError } from "@/types/masters";

// ─── URL serialisation helpers (UR-S3-004) ───────────────────────────────────

function filtersToSearchParams(filters: SalesReportFilters): URLSearchParams {
  const p = new URLSearchParams();
  if (filters.dateFrom)  p.set("date_from", filters.dateFrom);
  if (filters.dateTo)    p.set("date_to",   filters.dateTo);
  filters.dealerIds?.forEach((id) => p.append("dealer_ids", String(id)));
  filters.places?.forEach((pl) => p.append("places", pl));
  filters.designIds?.forEach((id) => p.append("design_ids", String(id)));
  return p;
}

function searchParamsToFilters(sp: URLSearchParams): SalesReportFilters {
  const filters: SalesReportFilters = {};
  if (sp.has("date_from")) filters.dateFrom  = sp.get("date_from")!;
  if (sp.has("date_to"))   filters.dateTo    = sp.get("date_to")!;
  const dIds = sp.getAll("dealer_ids").map(Number);
  if (dIds.length > 0) filters.dealerIds = dIds;
  const plc = sp.getAll("places");
  if (plc.length > 0) filters.places = plc;
  const desIds = sp.getAll("design_ids").map(Number);
  if (desIds.length > 0) filters.designIds = desIds;
  return filters;
}

// ─────────────────────────────────────────────────────────────────────────────

export function SalesReportView() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [filters, setFilters] = useState<SalesReportFilters>(() =>
    searchParamsToFilters(searchParams)
  );

  // URL sync — drop empty params (UR-S3-004).
  const syncUrl = useCallback(
    (f: SalesReportFilters) => {
      const p = filtersToSearchParams(f);
      const qs = p.toString();
      router.replace(qs ? `?${qs}` : "?", { scroll: false });
    },
    [router]
  );

  useEffect(() => {
    syncUrl(filters);
  }, [filters, syncUrl]);

  // Masters: dealers + designs (stale 60s — AC-046 dropdown sources).
  const { data: dealers = [] } = useQuery({
    queryKey: ["dealers"],
    queryFn: () => dealersApi.list(false),
    staleTime: 60_000,
  });

  const { data: designs = [] } = useQuery({
    queryKey: ["designs"],
    queryFn: () => designsApi.list(false),
    staleTime: 60_000,
  });

  // Derive places from loaded dealers (UR-S3-002).
  const places = [...new Set(dealers.map((d) => d.place))].sort();

  // Sales report query (stale 0 — must reflect latest data).
  const {
    data: report,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["sales-report", JSON.stringify(filters)],
    queryFn: () => getSalesReport(filters),
    staleTime: 0,
  });

  // Toast on error.
  useEffect(() => {
    if (isError && error) {
      const apiErr = error as unknown as ApiError;
      toast.error(apiErr.detail ?? "Failed to load sales report");
    }
  }, [isError, error]);

  const consolidation = report?.consolidation ?? [];
  const transactions  = report?.transactions  ?? [];

  const consolidationSum = consolidation.reduce((s, r) => s + r.total_nos, 0);
  const transactionsSum  = transactions.reduce((s, r) => s + r.nos, 0);

  const isEmpty =
    !isLoading && consolidation.length === 0 && transactions.length === 0;

  const handleApply = (newFilters: SalesReportFilters) => {
    setFilters(newFilters);
  };

  const handleReset = () => {
    setFilters({});
  };

  return (
    <div className="space-y-6">
      {/* Filter bar */}
      <SalesReportFilterBar
        initialFilters={filters}
        onApply={handleApply}
        onReset={handleReset}
        dealers={dealers}
        designs={designs}
        places={places}
      />

      {/* Reconciliation badge (ONE instance, UR-S3-003) — only after data loads */}
      {!isLoading && !isError && report && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Totals:</span>
          <ReconciliationBadge
            consolidationSum={consolidationSum}
            transactionsSum={transactionsSum}
          />
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div
          role="alert"
          className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive"
        >
          {(error as unknown as ApiError)?.detail ?? "Failed to load report data. Please try again."}
        </div>
      )}

      {/* Empty state (both arrays empty) */}
      {isEmpty && !isError && (
        <EmptyReportState onClear={handleReset} />
      )}

      {/* AC-049: Consolidation FIRST, then Transactions — same scroll, no tabs */}
      {!isEmpty && (
        <>
          <section aria-labelledby="consolidation-h">
            <h2
              id="consolidation-h"
              className="text-base font-semibold mb-3"
            >
              Consolidation
            </h2>
            <ConsolidationTable rows={consolidation} isLoading={isLoading} />
          </section>

          <section aria-labelledby="transactions-h">
            <h2
              id="transactions-h"
              className="text-base font-semibold mb-3"
            >
              Transactions
            </h2>
            <TransactionsTable rows={transactions} isLoading={isLoading} />
          </section>
        </>
      )}
    </div>
  );
}
