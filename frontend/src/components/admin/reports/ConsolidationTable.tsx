"use client";

// S3 — Consolidation table for sales report (F-011, AC-047, AC-049).
// 4 visible columns: Design Name, Size, Grade, Total Nos.
// Footer row shows sum of total_nos (used by ReconciliationBadge in parent).
// Server pre-sorts by (design_name ASC, grade_code ASC) per RULE-019; component does NOT re-sort.

import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import type { ConsolidationRow } from "@/types/reports";

interface ConsolidationTableProps {
  rows: ConsolidationRow[];
  isLoading: boolean;
}

const SKELETON_COUNT = 4;

export function ConsolidationTable({ rows, isLoading }: ConsolidationTableProps) {
  const totalNos = rows.reduce((s, r) => s + r.total_nos, 0);

  return (
    <div className="overflow-x-auto rounded-md border">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50">
            <TableHead className="sticky left-0 bg-muted/50 z-10 text-xs uppercase tracking-wider font-medium text-muted-foreground min-w-[140px]">
              Design Name
            </TableHead>
            <TableHead className="text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Size
            </TableHead>
            <TableHead className="text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Grade
            </TableHead>
            <TableHead className="text-right text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Total Nos
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            Array.from({ length: SKELETON_COUNT }).map((_, i) => (
              <TableRow key={`skeleton-${i}`}>
                <TableCell className="sticky left-0 bg-background z-10">
                  <Skeleton className="h-4 w-32" />
                </TableCell>
                <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                <TableCell className="text-right"><Skeleton className="h-4 w-12 ml-auto" /></TableCell>
              </TableRow>
            ))
          ) : rows.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={4}
                className="text-center p-8 text-muted-foreground"
              >
                No matching sales.
              </TableCell>
            </TableRow>
          ) : (
            rows.map((row) => (
              <TableRow
                key={`${row.design_id}-${row.grade_id}`}
                className="border-b hover:bg-muted/30"
              >
                <TableCell className="sticky left-0 bg-background z-10 font-medium">
                  {row.design_name}
                </TableCell>
                <TableCell>{row.size}</TableCell>
                <TableCell>{row.grade_code}</TableCell>
                <TableCell className="text-right tabular-nums">{row.total_nos}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
        {!isLoading && rows.length > 0 && (
          <TableFooter>
            <TableRow className="bg-muted/50 font-medium">
              <TableCell
                colSpan={3}
                className="sticky left-0 bg-muted/50 z-10 text-sm"
              >
                Total
              </TableCell>
              <TableCell className="text-right tabular-nums text-sm">
                {totalNos}
              </TableCell>
            </TableRow>
          </TableFooter>
        )}
      </Table>
    </div>
  );
}
