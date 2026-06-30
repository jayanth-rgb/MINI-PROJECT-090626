"use client";

// S3 — Sales report filter bar (F-011, AC-046).
// 5 controls: Date From, Date To, Dealers (multi), Places (multi), Designs (multi).
// Draft state is LOCAL — only propagated to parent on Apply click to avoid per-keystroke refetches.
// Mobile: stacks vertically; tablet+: 2-col grid; desktop: single row flex-wrap.
// UR-S3-001: uses Dealer and Design (frontend type names), not DealerRead/TradingDesignRead.
// UR-S3-002: places list derived from dealers.map(d=>d.place) in parent, passed in as prop.

import { useState } from "react";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import {
  MultiSelectCombobox,
  type MultiSelectOption,
} from "@/components/ui/MultiSelectCombobox";
import type { SalesReportFilters } from "@/types/reports";
import type { Dealer, Design } from "@/types/masters";

interface SalesReportFilterBarProps {
  initialFilters: SalesReportFilters;
  onApply: (filters: SalesReportFilters) => void;
  onReset: () => void;
  dealers: Dealer[];
  designs: Design[];
  places: string[];
}

export function SalesReportFilterBar({
  initialFilters,
  onApply,
  onReset,
  dealers,
  designs,
  places,
}: SalesReportFilterBarProps) {
  const [draft, setDraft] = useState<SalesReportFilters>(initialFilters);

  const dealerOptions: MultiSelectOption[] = dealers.map((d) => ({
    value: d.dealer_id,
    label: d.dealer_name,
  }));

  const placeOptions: MultiSelectOption[] = places.map((p) => ({
    value: p,
    label: p,
  }));

  const designOptions: MultiSelectOption[] = designs.map((d) => ({
    value: d.design_id,
    label: d.design_name,
  }));

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    onApply(draft);
  };

  const handleReset = () => {
    const empty: SalesReportFilters = {};
    setDraft(empty);
    onReset();
  };

  return (
    <form
      onSubmit={handleApply}
      className="rounded-lg border bg-card p-4"
      aria-label="Sales report filters"
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:flex lg:flex-wrap lg:items-end lg:gap-4">
        {/* Date From */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="filter-date-from" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Date From
          </Label>
          <DatePicker
            id="filter-date-from"
            value={draft.dateFrom}
            onChange={(iso) => setDraft((d) => ({ ...d, dateFrom: iso ?? undefined }))}
            placeholder="From"
          />
        </div>

        {/* Date To */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="filter-date-to" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Date To
          </Label>
          <DatePicker
            id="filter-date-to"
            value={draft.dateTo}
            onChange={(iso) => setDraft((d) => ({ ...d, dateTo: iso ?? undefined }))}
            placeholder="To"
          />
        </div>

        {/* Dealers */}
        <div className="flex flex-col gap-1.5">
          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Dealers
          </Label>
          <MultiSelectCombobox
            options={dealerOptions}
            value={draft.dealerIds ?? []}
            onChange={(next) =>
              setDraft((d) => ({ ...d, dealerIds: next as number[] }))
            }
            placeholder="All dealers"
            data-testid="filter-dealers"
          />
        </div>

        {/* Places — derived from loaded dealers (UR-S3-002) */}
        <div className="flex flex-col gap-1.5">
          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Places
          </Label>
          <MultiSelectCombobox
            options={placeOptions}
            value={draft.places ?? []}
            onChange={(next) =>
              setDraft((d) => ({ ...d, places: next as string[] }))
            }
            placeholder="All places"
            data-testid="filter-places"
          />
        </div>

        {/* Designs */}
        <div className="flex flex-col gap-1.5">
          <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Designs
          </Label>
          <MultiSelectCombobox
            options={designOptions}
            value={draft.designIds ?? []}
            onChange={(next) =>
              setDraft((d) => ({ ...d, designIds: next as number[] }))
            }
            placeholder="All designs"
            data-testid="filter-designs"
          />
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 lg:ml-auto">
          <Button
            type="submit"
            size="sm"
            className="flex-1 lg:flex-none"
          >
            Apply
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleReset}
            className="flex-1 lg:flex-none"
          >
            Reset
          </Button>
        </div>
      </div>
    </form>
  );
}
