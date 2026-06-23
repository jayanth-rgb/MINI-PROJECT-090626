"use client";

import { useState } from "react";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface DatePickerProps {
  value?: string; // ISO date YYYY-MM-DD
  onChange: (iso: string | undefined) => void;
  minDate?: Date;
  maxDate?: Date;
  placeholder?: string;
  id?: string;
  ariaInvalid?: boolean;
  ariaDescribedBy?: string;
}

function toDate(iso?: string): Date | undefined {
  if (!iso) return undefined;
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function toISO(d?: Date): string | undefined {
  if (!d) return undefined;
  return format(d, "yyyy-MM-dd");
}

export function DatePicker({
  value,
  onChange,
  minDate,
  maxDate,
  placeholder = "Pick a date",
  id,
  ariaInvalid,
  ariaDescribedBy,
}: DatePickerProps) {
  const [open, setOpen] = useState(false);
  const selected = toDate(value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          id={id}
          type="button"
          variant="outline"
          aria-invalid={ariaInvalid}
          aria-describedby={ariaDescribedBy}
          className={cn(
            "w-full justify-start text-left font-normal",
            !selected && "text-muted-foreground"
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {selected ? format(selected, "PPP") : <span>{placeholder}</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          selected={selected}
          onSelect={(d) => {
            onChange(toISO(d));
            setOpen(false);
          }}
          disabled={(d) =>
            (minDate ? d < minDate : false) || (maxDate ? d > maxDate : false)
          }
          autoFocus
        />
      </PopoverContent>
    </Popover>
  );
}
