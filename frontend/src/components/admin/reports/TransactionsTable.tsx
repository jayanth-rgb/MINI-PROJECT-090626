"use client";

// S3 — Transactions table for sales report (F-011, AC-048, AC-049).
// 7 visible columns: Date, Dealer, Place, Design+Size, Grade, Nos.
// Mobile: hides Place and Size columns by default.
// Footer row shows sum-of-nos (for ReconciliationBadge AC-050 verification in parent).
// Server pre-sorts by (sales_date ASC, header_id ASC) per RULE-020; component does NOT re-sort.

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
import type { TransactionRow } from "@/types/reports";

interface TransactionsTableProps {
  rows: TransactionRow[];
  isLoading: boolean;
}

const SKELETON_COUNT = 5;

export function TransactionsTable({ rows, isLoading }: TransactionsTableProps) {
  const totalNos = rows.reduce((s, r) => s + r.nos, 0);

  return (
    <div className="overflow-x-auto rounded-md border">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50">
            <TableHead className="text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Date
            </TableHead>
            <TableHead className="text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Dealer
            </TableHead>
            {/* Place hidden on mobile */}
            <TableHead className="hidden sm:table-cell text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Place
            </TableHead>
            <TableHead className="text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Design
            </TableHead>
            {/* Size hidden on mobile */}
            <TableHead className="hidden sm:table-cell text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Size
            </TableHead>
            <TableHead className="text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Grade
            </TableHead>
            <TableHead className="text-right text-xs uppercase tracking-wider font-medium text-muted-foreground">
              Nos
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            Array.from({ length: SKELETON_COUNT }).map((_, i) => (
              <TableRow key={`skeleton-${i}`}>
                <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                <TableCell className="hidden sm:table-cell"><Skeleton className="h-4 w-16" /></TableCell>
                <TableCell><Skeleton className="h-4 w-28" /></TableCell>
                <TableCell className="hidden sm:table-cell"><Skeleton className="h-4 w-12" /></TableCell>
                <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                <TableCell className="text-right"><Skeleton className="h-4 w-10 ml-auto" /></TableCell>
              </TableRow>
            ))
          ) : rows.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={7}
                className="text-center p-8 text-muted-foreground"
              >
                No matching transactions.
              </TableCell>
            </TableRow>
          ) : (
            rows.map((row, i) => (
              <TableRow
                key={`${row.sales_date}-${row.dealer_id}-${row.design_id}-${row.grade_id}-${i}`}
                className="border-b hover:bg-muted/30"
              >
                <TableCell>
                  <abbr title="ISO date" className="no-underline">
                    {row.sales_date}
                  </abbr>
                </TableCell>
                <TableCell>{row.dealer_name}</TableCell>
                <TableCell className="hidden sm:table-cell">{row.place}</TableCell>
                <TableCell>{row.design_name}</TableCell>
                <TableCell className="hidden sm:table-cell">{row.size}</TableCell>
                <TableCell>{row.grade_code}</TableCell>
                <TableCell className="text-right tabular-nums">{row.nos}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
        {!isLoading && rows.length > 0 && (
          <TableFooter>
            <TableRow className="bg-muted/50 font-medium">
              <TableCell colSpan={6} className="text-sm">
                Total
              </TableCell>
              {/* Account for hidden columns on mobile — colspan shifts */}
              <TableCell className="text-right tabular-nums text-sm hidden sm:table-cell" colSpan={1}>
                {totalNos}
              </TableCell>
              {/* Mobile: single colspan for all hidden cols */}
              <TableCell className="text-right tabular-nums text-sm sm:hidden">
                {totalNos}
              </TableCell>
            </TableRow>
          </TableFooter>
        )}
      </Table>
    </div>
  );
}
