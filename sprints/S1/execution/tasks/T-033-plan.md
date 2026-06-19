# T-033 — MasterDataTable

**Module:** M-006 · **Depends on:** — · **TC refs:** — (covered indirectly by TC-040) · **AC:** AC-002/005/008/012/015/017

## Implementation logic

```tsx
// frontend/src/components/admin/MasterDataTable.tsx
"use client";

import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Column<T> { key: keyof T; label: string; }

interface Props<T> {
  rows: T[];
  columns: Column<T>[];
  rowKey: (row: T) => string | number;
  isActive: (row: T) => boolean;
  onEdit: (row: T) => void;
  onToggleActive: (row: T) => void;
}

export function MasterDataTable<T>({
  rows, columns, rowKey, isActive, onEdit, onToggleActive,
}: Props<T>) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((c) => (
            <TableHead key={String(c.key)}>{c.label}</TableHead>
          ))}
          <TableHead className="w-48 text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow
            key={rowKey(row)}
            className={cn(!isActive(row) && "text-muted-foreground opacity-60")}
          >
            {columns.map((c) => (
              <TableCell key={String(c.key)}>{String(row[c.key] ?? "")}</TableCell>
            ))}
            <TableCell className="space-x-2 text-right">
              <Button variant="ghost" size="sm" onClick={() => onEdit(row)}>Edit</Button>
              <Button
                variant={isActive(row) ? "destructive" : "secondary"}
                size="sm"
                onClick={() => onToggleActive(row)}
              >
                {isActive(row) ? "Deactivate" : "Reactivate"}
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

## Constraints
- Generic over T — pages pass concrete row type
- Inactive rows muted via Tailwind opacity + muted-foreground (used in TC-040)

## Do not touch
Any other file.

## Success criteria
- **Manual:** Edit button calls onEdit; Deactivate triggers onToggleActive
- **Automated:** TC-040 (deactivate flow incl. muted-row render)
- **DoD:** Generic + Actions column always last + inactive style

## Checkout prompt
*"MasterDataTable — generic table with Edit + Activate/Deactivate actions."*
