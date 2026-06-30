"use client";

// S3 — Reusable multi-select combobox (F-011, TD-010).
// Built on Radix Popover + native search input.
//
// TD-010 TEST SHIM: jsdom cannot drive Radix Popover internals. Tests should
// either mock this module entirely OR import MultiSelectComboboxFallback (a
// native <select multiple>) for assertion. The NODE_ENV check below
// automatically enables the fallback in test environments.
//
// Usage:
//   import { MultiSelectCombobox } from "@/components/ui/MultiSelectCombobox";
// For test files:
//   import { MultiSelectComboboxFallback } from "@/components/ui/MultiSelectCombobox";

import { useState } from "react";
import { Check, ChevronDown, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export interface MultiSelectOption {
  value: string | number;
  label: string;
}

export interface MultiSelectComboboxProps {
  options: MultiSelectOption[];
  value: Array<string | number>;
  onChange: (next: Array<string | number>) => void;
  placeholder: string;
  emptyMessage?: string;
  searchable?: boolean;
  /** Data-testid forwarded to the trigger button (used in tests). */
  "data-testid"?: string;
}

// ── Radix-Popover version (runtime) ──────────────────────────────────────────

export function MultiSelectCombobox({
  options,
  value,
  onChange,
  placeholder,
  emptyMessage = "No options found.",
  searchable = true,
  "data-testid": testId,
}: MultiSelectComboboxProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const filtered = searchable
    ? options.filter((o) =>
        String(o.label).toLowerCase().includes(search.toLowerCase())
      )
    : options;

  const toggle = (optValue: string | number) => {
    if (value.includes(optValue)) {
      onChange(value.filter((v) => v !== optValue));
    } else {
      onChange([...value, optValue]);
    }
  };

  const remove = (optValue: string | number) => {
    onChange(value.filter((v) => v !== optValue));
  };

  const selectedLabels = value
    .map((v) => options.find((o) => o.value === v)?.label ?? String(v));

  return (
    <div className="flex flex-col gap-1.5">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-haspopup="listbox"
            aria-multiselectable="true"
            aria-expanded={open}
            className="w-full sm:w-[180px] justify-between font-normal"
            data-testid={testId}
          >
            <span className="truncate text-muted-foreground">
              {value.length > 0
                ? `${value.length} selected`
                : placeholder}
            </span>
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[220px] p-2" align="start">
          {searchable && (
            <Input
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="mb-2 h-7 text-sm"
              aria-label={`Search ${placeholder}`}
            />
          )}
          {filtered.length === 0 ? (
            <p className="py-2 text-center text-sm text-muted-foreground">
              {emptyMessage}
            </p>
          ) : (
            <ul role="listbox" aria-multiselectable="true" className="max-h-48 overflow-y-auto">
              {filtered.map((option) => {
                const isSelected = value.includes(option.value);
                return (
                  <li
                    key={String(option.value)}
                    role="option"
                    aria-selected={isSelected}
                    className={cn(
                      "flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground",
                      isSelected && "bg-accent/50"
                    )}
                    onClick={() => toggle(option.value)}
                  >
                    <span
                      className={cn(
                        "flex h-4 w-4 shrink-0 items-center justify-center rounded border border-input",
                        isSelected && "border-primary bg-primary text-primary-foreground"
                      )}
                    >
                      {isSelected && <Check className="h-3 w-3" />}
                    </span>
                    {option.label}
                  </li>
                );
              })}
            </ul>
          )}
        </PopoverContent>
      </Popover>

      {/* Chip pills for selected values */}
      {value.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {selectedLabels.map((label, i) => (
            <Badge
              key={String(value[i])}
              variant="secondary"
              className="gap-1 pr-1"
            >
              {label}
              <button
                type="button"
                aria-label={`Remove ${label}`}
                onClick={() => remove(value[i])}
                className="ml-0.5 rounded-sm opacity-70 hover:opacity-100 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Native <select multiple> fallback — for jsdom / test environments (TD-010) ─

export interface MultiSelectComboboxFallbackProps {
  options: MultiSelectOption[];
  value: Array<string | number>;
  onChange: (next: Array<string | number>) => void;
  placeholder?: string;
  "data-testid"?: string;
}

/**
 * Native multi-select shim. Import this in test files where Radix Popover
 * internals are unavailable. Identical value-contract to MultiSelectCombobox.
 */
export function MultiSelectComboboxFallback({
  options,
  value,
  onChange,
  placeholder,
  "data-testid": testId,
}: MultiSelectComboboxFallbackProps) {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selected = Array.from(e.target.selectedOptions).map((o) => {
      // Coerce back to number if the original option.value was a number.
      const num = Number(o.value);
      return Number.isNaN(num) ? o.value : num;
    });
    onChange(selected);
  };

  return (
    <select
      multiple
      data-testid={testId}
      aria-label={placeholder}
      value={value.map(String)}
      onChange={handleChange}
      className="w-full rounded border border-input bg-background p-1 text-sm"
    >
      {options.map((o) => (
        <option key={String(o.value)} value={String(o.value)}>
          {o.label}
        </option>
      ))}
    </select>
  );
}
