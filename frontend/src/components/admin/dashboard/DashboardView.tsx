"use client";

// S3 — Dashboard container component (F-010).
// Owns asOfDate state, URL-syncs via useSearchParams + router.replace.
// Drives DashboardDatePicker + DashboardTable + empty/error states.

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { getDashboard } from "@/lib/api/dashboard";
import { DashboardDatePicker } from "./DashboardDatePicker";
import { DashboardTable } from "./DashboardTable";
import type { ApiError } from "@/types/masters";

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export function DashboardView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const qc = useQueryClient();

  // Initialise from URL or fall back to today (UR-S3-004: drop empty params on write).
  const [asOfDate, setAsOfDate] = useState<string>(
    () => searchParams.get("as_of_date") ?? todayISO()
  );

  // Sync URL when asOfDate changes.
  const syncUrl = useCallback(
    (date: string) => {
      const params = new URLSearchParams();
      params.set("as_of_date", date);
      router.replace(`?${params.toString()}`, { scroll: false });
    },
    [router]
  );

  useEffect(() => {
    syncUrl(asOfDate);
  }, [asOfDate, syncUrl]);

  const { data: rows = [], isLoading, isError, error } = useQuery({
    queryKey: ["dashboard", asOfDate],
    queryFn: () => getDashboard(asOfDate),
    staleTime: 0, // Always refetch — dashboard must reflect latest data.
  });

  // Toast on error.
  useEffect(() => {
    if (isError && error) {
      const apiErr = error as unknown as ApiError;
      toast.error(apiErr.detail ?? "Failed to load dashboard");
    }
  }, [isError, error]);

  const handleDateChange = (newDate: string) => {
    setAsOfDate(newDate);
  };

  const handleRefresh = () => {
    qc.invalidateQueries({ queryKey: ["dashboard", asOfDate] });
  };

  return (
    <div className="space-y-4">
      {/* Header row: date picker + refresh button */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 px-0">
        <div className="flex flex-col sm:flex-row sm:items-center gap-2 flex-1">
          <label
            htmlFor="dashboard-as-of-date"
            className="text-sm font-medium text-muted-foreground whitespace-nowrap"
          >
            As of date
          </label>
          <DashboardDatePicker value={asOfDate} onChange={handleDateChange} />
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          aria-label="Refresh dashboard"
          className="w-full sm:w-auto"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Error state */}
      {isError && (
        <div
          role="alert"
          className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive"
        >
          {(error as unknown as ApiError)?.detail ?? "Failed to load dashboard data. Please try refreshing."}
        </div>
      )}

      {/* Table (handles isLoading + empty internally) */}
      <DashboardTable rows={rows} isLoading={isLoading} />
    </div>
  );
}
