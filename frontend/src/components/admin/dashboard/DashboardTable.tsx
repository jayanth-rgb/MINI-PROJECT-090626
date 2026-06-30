"use client";

// S3 — Stock dashboard table (F-010, AC-041–AC-044).
// 8 visible columns: Design Name, Size, Grade, Opening, Inward, Outward, Adjust, Closing.
// design_id + grade_id used as row key only (not displayed).
// Server pre-sorts by (design_name ASC, grade_code ASC); component does NOT re-sort.

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import type { DashboardRow } from "@/types/dashboard";
import { EmptyDashboardState } from "./EmptyDashboardState";

interface DashboardTableProps {
  rows: DashboardRow[];
  isLoading: boolean;
}

// Number of skeleton rows: 6 on tablet+, 3 on mobile (handled via CSS).
const SKELETON_COUNT = 6;

export function DashboardTable({ rows, isLoading }: DashboardTableProps) {
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
              Opening
            </TableHead>
            <TableHead className="text-right text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Inward
            </TableHead>
            <TableHead className="text-right text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Outward
            </TableHead>
            <TableHead className="text-right text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Adjust
            </TableHead>
            <TableHead className="text-right text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Closing
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            Array.from({ length: SKELETON_COUNT }).map((_, i) => (
              <TableRow key={`skeleton-${i}`} className={i >= 3 ? "hidden sm:table-row" : ""}>
                <TableCell className="sticky left-0 bg-background z-10">
                  <Skeleton className="h-4 w-32" />
                </TableCell>
                <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                <TableCell className="text-right"><Skeleton className="h-4 w-12 ml-auto" /></TableCell>
                <TableCell className="text-right"><Skeleton className="h-4 w-12 ml-auto" /></TableCell>
                <TableCell className="text-right"><Skeleton className="h-4 w-12 ml-auto" /></TableCell>
                <TableCell className="text-right"><Skeleton className="h-4 w-12 ml-auto" /></TableCell>
                <TableCell className="text-right"><Skeleton className="h-4 w-12 ml-auto" /></TableCell>
              </TableRow>
            ))
          ) : rows.length === 0 ? (
            <TableRow>
              <TableCell colSpan={8} className="p-0">
                <EmptyDashboardState />
              </TableCell>
            </TableRow>
          ) : (
            rows.map((row) => (
              <TableRow
                key={`${row.design_id}-${row.grade_id}`}
                className="border-b hover:bg-muted/30"
              >
                <TableCell
                  className="sticky left-0 bg-background z-10 font-medium"
                  // First cell of each row is the row identity
                >
                  {row.design_name}
                </TableCell>
                <TableCell>{row.size}</TableCell>
                <TableCell>{row.grade_code}</TableCell>
                <TableCell className="text-right tabular-nums">{row.opening}</TableCell>
                <TableCell className="text-right tabular-nums">{row.inward}</TableCell>
                <TableCell className="text-right tabular-nums">{row.outward}</TableCell>
                <TableCell className="text-right tabular-nums">{row.adjust}</TableCell>
                <TableCell className="text-right tabular-nums font-medium">{row.closing}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
