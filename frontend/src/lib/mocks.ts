// Mock data + helpers backing the scaffold-phase API boundary at
// frontend/src/lib/api/masters.ts. This file is deleted by Sonnet during
// /ases-dev once masters.ts is rewritten to call the live FastAPI backend.
//
// Seed contents mirror PRD AC-003/006/009/010/014/018 so the scaffold matches
// what /backend/scripts/seed_master_data.py will populate in the real DB.
//
// S3 additions (appended below): MOCK_DASHBOARD_ROWS + extended MOCK_SALES_REPORT_ROWS

import type {
  Supplier,
  Staff,
  Dealer,
  Grade,
  Design,
  DesignGradeMap,
  ApiError,
} from "@/types/masters";
import type {
  InwardRead,
  SalesRead,
  AdjustmentRead,
  DesignGradeReadWithCb,
} from "@/types/transactions";

const ISO_NOW = "2026-06-09T00:00:00Z";

// ---- in-memory tables --------------------------------------------------------

export const MOCK_SUPPLIERS: Supplier[] = [
  { supplier_id: 1, supplier_name: "Manjunatha", place: "Mallur", is_active: true, created_at: ISO_NOW },
  { supplier_id: 2, supplier_name: "Dinnesh Reddy", place: "Mallur", is_active: true, created_at: ISO_NOW },
  { supplier_id: 3, supplier_name: "Antony Tiles", place: "Kerala", is_active: true, created_at: ISO_NOW },
];

export const MOCK_STAFF: Staff[] = [
  "Chandran",
  "Jayapal",
  "Ramachandraiah",
  "Sujatha",
  "Ramya",
  "Vijay",
  "Sajil",
  "Ashu",
  "Amaresh",
].map((name, i) => ({
  staff_id: i + 1,
  staff_name: name,
  is_active: true,
  created_at: ISO_NOW,
}));

export const MOCK_DEALERS: Dealer[] = [
  { dealer_id: 1, dealer_name: "Raj Hardwares", place: "Dindivanam", is_active: true, created_at: ISO_NOW },
  { dealer_id: 2, dealer_name: "Tiles Mart", place: "Attibelle", is_active: true, created_at: ISO_NOW },
  { dealer_id: 3, dealer_name: "Shanmugam & Co", place: "Coimbatore", is_active: true, created_at: ISO_NOW },
];

export const MOCK_GRADES: Grade[] = [
  "1", "2", "2A", "4", "5", "6", "1OB", "OB", "DIM",
].map((code, i) => ({
  grade_id: i + 1,
  grade_code: code,
  is_active: true,
}));

export const MOCK_DESIGNS: Design[] = [
  { design_id: 1, size: "16X10", design_name: "16X10 Ridges", is_active: true, created_at: ISO_NOW },
  { design_id: 2, size: "12X8", design_name: "12X8 Ridges", is_active: true, created_at: ISO_NOW },
  { design_id: 3, size: "11X7", design_name: "11X7 Ridges", is_active: true, created_at: ISO_NOW },
];

const designByName = (name: string) =>
  MOCK_DESIGNS.find((d) => d.design_name === name)!.design_id;
const gradeByCode = (code: string) =>
  MOCK_GRADES.find((g) => g.grade_code === code)!.grade_id;

export const MOCK_DESIGN_GRADE_MAP: DesignGradeMap[] = [
  ["16X10 Ridges", "1"],
  ["16X10 Ridges", "2"],
  ["12X8 Ridges", "1"],
  ["12X8 Ridges", "OB"],
  ["11X7 Ridges", "1"],
  ["11X7 Ridges", "2"],
].map(([designName, gradeCode], i) => ({
  map_id: i + 1,
  design_id: designByName(designName as string),
  grade_id: gradeByCode(gradeCode as string),
  is_active: true,
  design_name: designName as string,
  grade_code: gradeCode as string,
}));

// ---- helpers -----------------------------------------------------------------

export function nextId<T>(rows: T[], key: keyof T): number {
  if (rows.length === 0) return 1;
  return (
    Math.max(...rows.map((r) => Number(r[key]) || 0)) + 1
  );
}

export async function delay(ms = 120): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

// Synthetic API error — shape matches lib/api/client.ts interceptor output
// (UR-W004 fix: { status, detail } so the same toast handler works under
// mock and integrated modes).
export function throwApiError(status: number, detail: string): never {
  const err: ApiError = { status, detail };
  throw err;
}

// Hydration helper for design-grade-map rows.
export function hydrateMapRow(row: DesignGradeMap): DesignGradeMap {
  const design = MOCK_DESIGNS.find((d) => d.design_id === row.design_id);
  const grade = MOCK_GRADES.find((g) => g.grade_id === row.grade_id);
  return {
    ...row,
    design_name: design?.design_name,
    grade_code: grade?.grade_code,
  };
}

// ============================================================================
// S2 — transaction tables (in-memory) for scaffold-phase mocks
// ============================================================================

export const MOCK_INWARDS: InwardRead[] = [];
export const MOCK_SALES: SalesRead[] = [];
export const MOCK_ADJUSTMENTS: AdjustmentRead[] = [];

// Per-(design, grade) running balance (driven by Inward/Sales/Adjustment writes).
// Used by getGradesWithCb mock to project software_cb at request time.
export const MOCK_RUNNING_BALANCE: Map<string, number> = new Map();

export function balanceKey(designId: number, gradeId: number): string {
  return `${designId}:${gradeId}`;
}

export function bumpBalance(designId: number, gradeId: number, delta: number): number {
  const key = balanceKey(designId, gradeId);
  const next = (MOCK_RUNNING_BALANCE.get(key) ?? 0) + delta;
  MOCK_RUNNING_BALANCE.set(key, next);
  return next;
}

export function getBalance(designId: number, gradeId: number): number {
  return MOCK_RUNNING_BALANCE.get(balanceKey(designId, gradeId)) ?? 0;
}

// DF-003 projection: returns active (design, grade) mappings + current software_cb.
// In integrated mode this hits GET /api/v1/designs/{id}/grades-with-cb (T-055).
export function projectGradesWithCb(designId: number): DesignGradeReadWithCb[] {
  return MOCK_DESIGN_GRADE_MAP.filter(
    (m) => m.design_id === designId && m.is_active
  )
    .map((m) => {
      const grade = MOCK_GRADES.find(
        (g) => g.grade_id === m.grade_id && g.is_active
      );
      if (!grade) return null;
      return {
        grade_id: grade.grade_id,
        grade_code: grade.grade_code,
        software_cb: getBalance(designId, grade.grade_id),
      };
    })
    .filter((r): r is DesignGradeReadWithCb => r !== null);
}

// ============================================================================
// S3 — Dashboard + Sales Report mock data (appended; do not remove S1/S2 data)
// ============================================================================

import type { DashboardRow } from "@/types/dashboard";
import type { TransactionRow } from "@/types/reports";

// 6 rows: design 1 (16X10 Ridges) × grades 1+2, design 2 (12X8 Ridges) × grades 1+OB,
// design 3 (11X7 Ridges) × grades 1+2. Varied numbers so every column renders non-trivially.
export const MOCK_DASHBOARD_ROWS: DashboardRow[] = [
  {
    design_id: 1,
    design_name: "16X10 Ridges",
    size: "16X10",
    grade_id: 1,
    grade_code: "1",
    opening: 120,
    inward: 200,
    outward: 150,
    adjust: -10,
    closing: 160,
  },
  {
    design_id: 1,
    design_name: "16X10 Ridges",
    size: "16X10",
    grade_id: 2,
    grade_code: "2",
    opening: 80,
    inward: 100,
    outward: 60,
    adjust: 0,
    closing: 120,
  },
  {
    design_id: 2,
    design_name: "12X8 Ridges",
    size: "12X8",
    grade_id: 1,
    grade_code: "1",
    opening: 0,
    inward: 300,
    outward: 200,
    adjust: 5,
    closing: 105,
  },
  {
    design_id: 2,
    design_name: "12X8 Ridges",
    size: "12X8",
    grade_id: 8,
    grade_code: "OB",
    opening: 50,
    inward: 0,
    outward: 30,
    adjust: 0,
    closing: 20,
  },
  {
    design_id: 3,
    design_name: "11X7 Ridges",
    size: "11X7",
    grade_id: 1,
    grade_code: "1",
    opening: 200,
    inward: 150,
    outward: 180,
    adjust: -5,
    closing: 165,
  },
  {
    design_id: 3,
    design_name: "11X7 Ridges",
    size: "11X7",
    grade_id: 2,
    grade_code: "2",
    opening: 60,
    inward: 40,
    outward: 20,
    adjust: 0,
    closing: 80,
  },
];

// Flat transaction rows for sales report mock. Multiple rows per (design, grade) pair
// so the consolidation grouping renders total_nos > any single row's nos (AC-050).
export const MOCK_SALES_REPORT_ROWS: TransactionRow[] = [
  {
    sales_date: "2026-06-10",
    dealer_id: 1,
    dealer_name: "Raj Hardwares",
    place: "Dindivanam",
    design_id: 1,
    design_name: "16X10 Ridges",
    size: "16X10",
    grade_id: 1,
    grade_code: "1",
    nos: 60,
  },
  {
    sales_date: "2026-06-12",
    dealer_id: 2,
    dealer_name: "Tiles Mart",
    place: "Attibelle",
    design_id: 1,
    design_name: "16X10 Ridges",
    size: "16X10",
    grade_id: 1,
    grade_code: "1",
    nos: 90,
  },
  {
    sales_date: "2026-06-13",
    dealer_id: 1,
    dealer_name: "Raj Hardwares",
    place: "Dindivanam",
    design_id: 1,
    design_name: "16X10 Ridges",
    size: "16X10",
    grade_id: 2,
    grade_code: "2",
    nos: 60,
  },
  {
    sales_date: "2026-06-14",
    dealer_id: 3,
    dealer_name: "Shanmugam & Co",
    place: "Coimbatore",
    design_id: 2,
    design_name: "12X8 Ridges",
    size: "12X8",
    grade_id: 1,
    grade_code: "1",
    nos: 100,
  },
  {
    sales_date: "2026-06-15",
    dealer_id: 2,
    dealer_name: "Tiles Mart",
    place: "Attibelle",
    design_id: 2,
    design_name: "12X8 Ridges",
    size: "12X8",
    grade_id: 1,
    grade_code: "1",
    nos: 100,
  },
  {
    sales_date: "2026-06-16",
    dealer_id: 3,
    dealer_name: "Shanmugam & Co",
    place: "Coimbatore",
    design_id: 3,
    design_name: "11X7 Ridges",
    size: "11X7",
    grade_id: 1,
    grade_code: "1",
    nos: 180,
  },
  {
    sales_date: "2026-06-17",
    dealer_id: 1,
    dealer_name: "Raj Hardwares",
    place: "Dindivanam",
    design_id: 3,
    design_name: "11X7 Ridges",
    size: "11X7",
    grade_id: 2,
    grade_code: "2",
    nos: 20,
  },
];
