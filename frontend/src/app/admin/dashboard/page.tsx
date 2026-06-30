// S3 — Stock Dashboard page (F-010). Server component wrapper.
// Route: /admin/dashboard
// Inherits app/admin/layout.tsx shell — no additional layout concerns.
// Suspense required: DashboardView uses useSearchParams() (Next.js 15 rule).

import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { DashboardView } from "@/components/admin/dashboard/DashboardView";

export const metadata = { title: "Stock Dashboard — Jayanth Trading" };

function DashboardFallback() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Stock Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Current stock position by design and grade.
        </p>
      </header>
      <Suspense fallback={<DashboardFallback />}>
        <DashboardView />
      </Suspense>
    </div>
  );
}
