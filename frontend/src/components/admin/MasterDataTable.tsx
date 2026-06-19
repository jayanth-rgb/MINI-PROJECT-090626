// T-033 — Generic master data table.
// Supports per-column `render` override (UR-W005 fix: is_active column renders
// a Badge rather than literal 'true'/'false').
"use client";

import { Pencil, Eye, EyeOff } from "lucide-react";
import type { ReactNode } from "react";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export interface MasterDataTableColumn<T> {
  key: keyof T;
  label: string;
  render?: (row: T) => ReactNode;
}

interface Props<T> {
  rows: T[];
  columns: MasterDataTableColumn<T>[];
  rowKey: (row: T) => string | number;
  isActive: (row: T) => boolean;
  onEdit: (row: T) => void;
  onToggleActive: (row: T) => void;
  isLoading?: boolean;
  testId?: string;
}

export function MasterDataTable<T>({
  rows,
  columns,
  rowKey,
  isActive,
  onEdit,
  onToggleActive,
  isLoading = false,
  testId = "master-data-table",
}: Props<T>) {
  return (
    <div className="overflow-x-auto rounded-md border" data-testid={testId}>
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50">
            {columns.map((c) => (
              <TableHead
                key={String(c.key)}
                className="text-xs uppercase tracking-wider font-medium text-muted-foreground"
              >
                {c.label}
              </TableHead>
            ))}
            <TableHead className="w-48 text-right text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Actions
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={`skeleton-${i}`}>
                {columns.map((c) => (
                  <TableCell key={String(c.key)}>
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                ))}
                <TableCell className="text-right">
                  <Skeleton className="h-8 w-32 ml-auto" />
                </TableCell>
              </TableRow>
            ))
          ) : rows.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={columns.length + 1}
                className="text-center p-8 text-muted-foreground"
              >
                No records found.
              </TableCell>
            </TableRow>
          ) : (
            rows.map((row) => {
              const active = isActive(row);
              return (
                <TableRow
                  key={rowKey(row)}
                  className={cn(
                    "border-b transition-colors",
                    active ? "hover:bg-muted/30" : "opacity-50 bg-muted/10"
                  )}
                  data-testid={`row-${rowKey(row)}`}
                >
                  {columns.map((c) => (
                    <TableCell key={String(c.key)}>
                      {c.render ? c.render(row) : renderDefaultCell(row[c.key])}
                    </TableCell>
                  ))}
                  <TableCell className="text-right space-x-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEdit(row)}
                      aria-label="Edit"
                      data-testid={`edit-btn-${rowKey(row)}`}
                    >
                      <Pencil className="h-4 w-4" />
                      <span className="ml-1 hidden sm:inline">Edit</span>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onToggleActive(row)}
                      aria-label={active ? "Deactivate" : "Reactivate"}
                      className={
                        active ? "text-destructive" : "text-emerald-600"
                      }
                      data-testid={`toggle-btn-${rowKey(row)}`}
                    >
                      {active ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                      <span className="ml-1 hidden sm:inline">
                        {active ? "Deactivate" : "Reactivate"}
                      </span>
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function renderDefaultCell(value: unknown): ReactNode {
  if (typeof value === "boolean") {
    // Fallback when caller forgets to pass a render override for is_active.
    return value ? (
      <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400 hover:bg-emerald-100">
        Active
      </Badge>
    ) : (
      <Badge variant="secondary">Inactive</Badge>
    );
  }
  return String(value ?? "");
}

// Helper exported for pages — drop-in `render` for the is_active column.
export function statusBadge(active: boolean): ReactNode {
  return active ? (
    <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400 hover:bg-emerald-100">
      Active
    </Badge>
  ) : (
    <Badge variant="secondary">Inactive</Badge>
  );
}
