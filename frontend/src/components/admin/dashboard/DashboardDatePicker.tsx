"use client";

// S3 — Dashboard as-of date picker (F-010).
// Wraps the existing shadcn DatePicker with an aria-label for accessibility.
// Props: value (ISO YYYY-MM-DD), onChange callback.

import { DatePicker } from "@/components/ui/date-picker";

interface DashboardDatePickerProps {
  value: string;
  onChange: (newDate: string) => void;
}

export function DashboardDatePicker({ value, onChange }: DashboardDatePickerProps) {
  return (
    <div className="w-full sm:w-[240px]">
      <DatePicker
        value={value}
        onChange={(iso) => {
          if (iso) onChange(iso);
        }}
        placeholder="Select date"
        id="dashboard-as-of-date"
        aria-label="Dashboard as-of date"
      />
    </div>
  );
}
