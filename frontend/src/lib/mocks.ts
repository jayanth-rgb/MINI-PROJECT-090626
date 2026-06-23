// Mock data + helpers backing the scaffold-phase API boundary at
// frontend/src/lib/api/masters.ts. This file is deleted by Sonnet during
// /ases-dev once masters.ts is rewritten to call the live FastAPI backend.
//
// Seed contents mirror PRD AC-003/006/009/010/014/018 so the scaffold matches
// what /backend/scripts/seed_master_data.py will populate in the real DB.

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
