"use client";

// S3 — Empty state for the stock dashboard (F-010).
// Renders when GET /dashboard returns [].

import Link from "next/link";

export function EmptyDashboardState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 max-w-[480px] mx-auto text-center">
      <p className="text-muted-foreground text-base">
        No active design-grade pairs yet.
      </p>
      <p className="text-muted-foreground text-sm mt-1">
        Create one in{" "}
        <Link
          href="/admin/design-grade-map"
          className="underline text-foreground hover:text-primary"
        >
          Admin &rarr; Design-Grade Mapping
        </Link>
        .
      </p>
    </div>
  );
}
