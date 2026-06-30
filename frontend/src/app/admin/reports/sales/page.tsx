// S3 — Sales Report page (F-011). Server component wrapper.
// Route: /admin/reports/sales
// Inherits app/admin/layout.tsx shell — no additional layout concerns.
// Suspense required: SalesReportView uses useSearchParams() (Next.js 15 rule).

import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { SalesReportView } from "@/components/admin/reports/SalesReportView";

export const metadata = { title: "Sales Report — Jayanth Trading" };

function SalesReportFallback() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-20 w-full" />
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}

export default function SalesReportPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Sales Report</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Filter sales by date range, dealer, place or design.
        </p>
      </header>
      <Suspense fallback={<SalesReportFallback />}>
        <SalesReportView />
      </Suspense>
    </div>
  );
}
