"use client";

// S3 — Reconciliation badge (F-011, AC-050, UR-S3-003).
// Displays the client-side AC-050 verification: sum(consolidation.total_nos) == sum(transactions.nos).
// Rendered ONCE near the filter bar — not duplicated in section headers (UR-S3-003).
// Server has already asserted AC-050; this badge provides visible PO confidence.

interface ReconciliationBadgeProps {
  consolidationSum: number;
  transactionsSum: number;
}

export function ReconciliationBadge({
  consolidationSum,
  transactionsSum,
}: ReconciliationBadgeProps) {
  const isReconciled = consolidationSum === transactionsSum;

  return (
    <span
      aria-live="polite"
      role="status"
      className={
        isReconciled
          ? "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400"
          : "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium bg-destructive/10 text-destructive"
      }
    >
      {isReconciled ? (
        <>Reconciled: {consolidationSum} / {transactionsSum} &#10003;</>
      ) : (
        <>&#9888; Mismatch: {consolidationSum} / {transactionsSum}</>
      )}
    </span>
  );
}
