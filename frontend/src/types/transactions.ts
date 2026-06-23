// S2 — TypeScript types mirroring backend Pydantic schemas in
// backend/src/presentation/schemas/transactions.py (T-046).
// `place` is server-derived per DS-013 (absent from *Create, present on *Read).
// `software_cb` on AdjustmentLine is server-snapshotted (absent from *Create).

// ───────────────────────────────────────────────────────────────────────────
// Inward (F-007)
// ───────────────────────────────────────────────────────────────────────────

export interface InwardLineCreate {
  design_id: number;
  grade_id: number;
  nos?: number | null;
}

export interface InwardCreate {
  purchase_date: string; // ISO date YYYY-MM-DD
  supplier_id: number;
  entered_by_id: number;
  lines: InwardLineCreate[];
}

export interface InwardLineRead {
  line_id: number;
  design_id: number;
  grade_id: number;
  nos: number;
}

export interface InwardRead {
  header_id: number;
  purchase_date: string;
  supplier_id: number;
  place: string;
  entered_by_id: number;
  created_at: string;
  lines: InwardLineRead[];
}

// ───────────────────────────────────────────────────────────────────────────
// Sales (F-008)
// ───────────────────────────────────────────────────────────────────────────

export interface SalesLineCreate {
  design_id: number;
  grade_id: number;
  nos?: number | null;
}

export interface SalesCreate {
  sales_date: string;
  dealer_id: number;
  loading_staff_id: number;
  verified_by_id: number;
  lines: SalesLineCreate[];
}

export interface SalesLineRead {
  line_id: number;
  design_id: number;
  grade_id: number;
  nos: number;
}

export interface SalesRead {
  header_id: number;
  sales_date: string;
  dealer_id: number;
  place: string;
  loading_staff_id: number;
  verified_by_id: number;
  created_at: string;
  lines: SalesLineRead[];
}

// ───────────────────────────────────────────────────────────────────────────
// Adjustment (F-009)
// ───────────────────────────────────────────────────────────────────────────

export interface AdjustmentLineCreate {
  grade_id: number;
  physical_cb: number;
}

export interface AdjustmentCreate {
  stock_date: string;
  entry_date: string;
  design_id: number;
  entered_by_id: number;
  lines: AdjustmentLineCreate[];
}

export interface AdjustmentLineRead {
  line_id: number;
  grade_id: number;
  software_cb: number;
  physical_cb: number;
  difference: number;
}

export interface AdjustmentRead {
  header_id: number;
  stock_date: string;
  entry_date: string;
  design_id: number;
  entered_by_id: number;
  created_at: string;
  lines: AdjustmentLineRead[];
}

// ───────────────────────────────────────────────────────────────────────────
// DF-003 contract — GET /designs/{id}/grades-with-cb response item
// ───────────────────────────────────────────────────────────────────────────

export interface DesignGradeReadWithCb {
  grade_id: number;
  grade_code: string;
  software_cb: number;
}
