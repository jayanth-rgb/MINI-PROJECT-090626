"use client";

import { AlertCircle } from "lucide-react";

interface Err012BannerProps {
  designName?: string;
}

export function Err012Banner({ designName }: Err012BannerProps) {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-lg border border-destructive/40 bg-destructive/10 p-4"
      data-testid="err-012-banner"
    >
      <AlertCircle className="h-5 w-5 shrink-0 text-destructive" aria-hidden="true" />
      <div className="space-y-1">
        <p className="font-medium text-destructive">
          No active grade combinations available
        </p>
        <p className="text-sm text-muted-foreground">
          {designName ? (
            <>
              <span className="font-medium">{designName}</span> has no active grade
              mappings.{" "}
            </>
          ) : (
            "The selected design has no active grade mappings. "
          )}
          Add a Design-Grade mapping in Admin → Design-Grade Map before adjusting
          stock for this design (ERR-012).
        </p>
      </div>
    </div>
  );
}
