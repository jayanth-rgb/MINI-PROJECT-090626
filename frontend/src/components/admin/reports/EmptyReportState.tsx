"use client";

// S3 — Empty state for the sales report (F-011).
// Renders when both consolidation and transactions results are empty after applying filters.

interface EmptyReportStateProps {
  onClear: () => void;
}

export function EmptyReportState({ onClear }: EmptyReportStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 max-w-[480px] mx-auto text-center">
      <p className="text-muted-foreground text-base">
        No sales match the current filters.
      </p>
      <p className="text-muted-foreground text-sm mt-1">
        Try clearing filters or widening the date range.
      </p>
      <button
        type="button"
        aria-label="Clear all filters"
        onClick={onClear}
        className="mt-4 inline-flex items-center rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium shadow-sm hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        Clear filters
      </button>
    </div>
  );
}
