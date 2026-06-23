"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface TransactionLineRowProps {
  index: number;
  gradeCode: string;
  value?: number | null;
  onChange: (v: number | null) => void;
  errorId?: string;
  errorMessage?: string;
}

export function TransactionLineRow({
  index,
  gradeCode,
  value,
  onChange,
  errorId,
  errorMessage,
}: TransactionLineRowProps) {
  const inputId = `line-${index}-nos`;
  return (
    <div className="grid grid-cols-2 items-center gap-3 sm:grid-cols-[1fr_minmax(0,200px)] sm:gap-4">
      <Label htmlFor={inputId} className="text-sm font-medium">
        Grade {gradeCode}
      </Label>
      <div>
        <Input
          id={inputId}
          type="number"
          min={0}
          step={1}
          inputMode="numeric"
          value={value ?? ""}
          aria-invalid={!!errorMessage}
          aria-describedby={errorMessage ? errorId : undefined}
          onChange={(e) => {
            const raw = e.target.value;
            if (raw === "") return onChange(null);
            const n = Number(raw);
            onChange(Number.isNaN(n) ? null : n);
          }}
          placeholder="0"
        />
        {errorMessage && (
          <p id={errorId} role="alert" className="mt-1 text-xs text-destructive">
            {errorMessage}
          </p>
        )}
      </div>
    </div>
  );
}
