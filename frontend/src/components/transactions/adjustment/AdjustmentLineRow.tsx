"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface AdjustmentLineRowProps {
  index: number;
  gradeCode: string;
  softwareCb: number;
  physicalCb?: number;
  onChange: (v: number | undefined) => void;
  errorId?: string;
  errorMessage?: string;
}

export function AdjustmentLineRow({
  index,
  gradeCode,
  softwareCb,
  physicalCb,
  onChange,
  errorId,
  errorMessage,
}: AdjustmentLineRowProps) {
  const inputId = `adj-line-${index}-physical`;
  const difference =
    physicalCb === undefined ? undefined : physicalCb - softwareCb;

  return (
    <div className="grid grid-cols-2 items-center gap-3 sm:grid-cols-[1fr_minmax(0,140px)_minmax(0,140px)_minmax(0,140px)] sm:gap-4">
      <Label htmlFor={inputId} className="text-sm font-medium">
        Grade {gradeCode}
      </Label>
      <div className="hidden sm:block text-sm" aria-label="software closing balance">
        <span className="text-xs text-muted-foreground">Software CB</span>
        <div className="font-mono">{softwareCb}</div>
      </div>
      <div>
        <Input
          id={inputId}
          type="number"
          min={0}
          step={1}
          inputMode="numeric"
          value={physicalCb ?? ""}
          aria-invalid={!!errorMessage}
          aria-describedby={errorMessage ? errorId : undefined}
          onChange={(e) => {
            const raw = e.target.value;
            if (raw === "") return onChange(undefined);
            const n = Number(raw);
            onChange(Number.isNaN(n) ? undefined : n);
          }}
          placeholder="Physical CB"
        />
        {errorMessage && (
          <p id={errorId} role="alert" className="mt-1 text-xs text-destructive">
            {errorMessage}
          </p>
        )}
      </div>
      <div className="text-sm" aria-live="polite">
        <span className="text-xs text-muted-foreground">Difference</span>
        <div
          className={
            "font-mono " +
            (difference === undefined
              ? "text-muted-foreground"
              : difference < 0
                ? "text-destructive"
                : difference > 0
                  ? "text-green-600 dark:text-green-400"
                  : "")
          }
          data-testid={`adj-line-${index}-difference`}
        >
          {difference === undefined ? "—" : difference}
        </div>
      </div>
    </div>
  );
}
