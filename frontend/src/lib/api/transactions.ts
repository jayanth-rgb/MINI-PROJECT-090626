// S2 — Integration boundary for transaction endpoints. The ONLY file Sonnet
// rewrites during /ases-dev (S3+) to swap mock helpers for real fetch() calls
// against the FastAPI backend at /api/v1/{inward,sales,adjustments,designs/.../grades-with-cb}.
//
// Every component/hook imports from this module; nothing imports from mocks.ts
// directly. Sonnet may delete mocks-helper imports once all functions here are
// swapped to apiClient.* calls.

import type {
  InwardCreate,
  InwardRead,
  SalesCreate,
  SalesRead,
  AdjustmentCreate,
  AdjustmentRead,
  DesignGradeReadWithCb,
} from "@/types/transactions";
import {
  MOCK_INWARDS,
  MOCK_SALES,
  MOCK_ADJUSTMENTS,
  MOCK_SUPPLIERS,
  MOCK_DEALERS,
  MOCK_STAFF,
  MOCK_DESIGNS,
  MOCK_GRADES,
  MOCK_DESIGN_GRADE_MAP,
  delay,
  nextId,
  bumpBalance,
  getBalance,
  projectGradesWithCb,
  throwApiError,
} from "@/lib/mocks";

const ISO_NOW = () => new Date().toISOString();

// ────────────────────────────────────────────────────────────────────────────
// inwardApi — /api/v1/inward (T-052 + T-047)
// ────────────────────────────────────────────────────────────────────────────

export const inwardApi = {
  async create(payload: InwardCreate): Promise<InwardRead> {
    await delay();
    const supplier = MOCK_SUPPLIERS.find(
      (s) => s.supplier_id === payload.supplier_id
    );
    if (!supplier) throwApiError(404, `Supplier ${payload.supplier_id} not found`);
    if (!supplier.is_active)
      throwApiError(422, `Supplier ${payload.supplier_id} is inactive`);
    const staff = MOCK_STAFF.find((s) => s.staff_id === payload.entered_by_id);
    if (!staff) throwApiError(404, `Staff ${payload.entered_by_id} not found`);
    if (!staff.is_active)
      throwApiError(422, `Staff ${payload.entered_by_id} is inactive`);

    // Strip nos == null || nos === 0 (RULE-017 / AC-025)
    const kept = payload.lines.filter((l) => l.nos != null && l.nos > 0);
    if (kept.length === 0)
      throwApiError(422, "at least one line with nos > 0 required");

    // Validate (design, grade) pair active (AC-023)
    for (const line of kept) {
      const pair = MOCK_DESIGN_GRADE_MAP.find(
        (m) =>
          m.design_id === line.design_id &&
          m.grade_id === line.grade_id &&
          m.is_active
      );
      if (!pair)
        throwApiError(
          422,
          `(design_id, grade_id) = (${line.design_id}, ${line.grade_id}) is not an active mapping`
        );
    }

    const header_id = nextId(MOCK_INWARDS, "header_id");
    const lineRows = kept.map((l, i) => ({
      line_id: i + 1,
      design_id: l.design_id,
      grade_id: l.grade_id,
      nos: l.nos!,
    }));
    // Apply ledger (Δ=+nos per line)
    for (const lr of lineRows) bumpBalance(lr.design_id, lr.grade_id, +lr.nos);

    const row: InwardRead = {
      header_id,
      purchase_date: payload.purchase_date,
      supplier_id: payload.supplier_id,
      place: supplier.place, // DS-013 snapshot
      entered_by_id: payload.entered_by_id,
      created_at: ISO_NOW(),
      lines: lineRows,
    };
    MOCK_INWARDS.push(row);
    return row;
  },

  async list(filters?: {
    date_from?: string;
    date_to?: string;
  }): Promise<InwardRead[]> {
    await delay();
    return MOCK_INWARDS.filter((r) => {
      if (filters?.date_from && r.purchase_date < filters.date_from) return false;
      if (filters?.date_to && r.purchase_date > filters.date_to) return false;
      return true;
    });
  },
};

// ────────────────────────────────────────────────────────────────────────────
// salesApi — /api/v1/sales (T-053 + T-048)
// ────────────────────────────────────────────────────────────────────────────

export const salesApi = {
  async create(payload: SalesCreate): Promise<SalesRead> {
    await delay();
    const dealer = MOCK_DEALERS.find((d) => d.dealer_id === payload.dealer_id);
    if (!dealer) throwApiError(404, `Dealer ${payload.dealer_id} not found`);
    if (!dealer.is_active)
      throwApiError(422, `Dealer ${payload.dealer_id} is inactive`);
    for (const staffId of [payload.loading_staff_id, payload.verified_by_id]) {
      const staff = MOCK_STAFF.find((s) => s.staff_id === staffId);
      if (!staff) throwApiError(404, `Staff ${staffId} not found`);
      if (!staff.is_active) throwApiError(422, `Staff ${staffId} is inactive`);
    }

    const kept = payload.lines.filter((l) => l.nos != null && l.nos > 0);
    if (kept.length === 0)
      throwApiError(422, "at least one line with nos > 0 required");

    for (const line of kept) {
      const pair = MOCK_DESIGN_GRADE_MAP.find(
        (m) =>
          m.design_id === line.design_id &&
          m.grade_id === line.grade_id &&
          m.is_active
      );
      if (!pair)
        throwApiError(
          422,
          `(design_id, grade_id) = (${line.design_id}, ${line.grade_id}) is not an active mapping`
        );
    }

    const header_id = nextId(MOCK_SALES, "header_id");
    const lineRows = kept.map((l, i) => ({
      line_id: i + 1,
      design_id: l.design_id,
      grade_id: l.grade_id,
      nos: l.nos!,
    }));
    // Apply ledger (Δ=−nos per line)
    for (const lr of lineRows) bumpBalance(lr.design_id, lr.grade_id, -lr.nos);

    const row: SalesRead = {
      header_id,
      sales_date: payload.sales_date,
      dealer_id: payload.dealer_id,
      place: dealer.place,
      loading_staff_id: payload.loading_staff_id,
      verified_by_id: payload.verified_by_id,
      created_at: ISO_NOW(),
      lines: lineRows,
    };
    MOCK_SALES.push(row);
    return row;
  },

  async list(filters?: {
    date_from?: string;
    date_to?: string;
    dealer_ids?: number[];
    design_ids?: number[];
  }): Promise<SalesRead[]> {
    await delay();
    return MOCK_SALES.filter((r) => {
      if (filters?.date_from && r.sales_date < filters.date_from) return false;
      if (filters?.date_to && r.sales_date > filters.date_to) return false;
      if (filters?.dealer_ids && !filters.dealer_ids.includes(r.dealer_id))
        return false;
      if (
        filters?.design_ids &&
        !r.lines.some((l) => filters.design_ids!.includes(l.design_id))
      )
        return false;
      return true;
    });
  },
};

// ────────────────────────────────────────────────────────────────────────────
// adjustmentsApi — /api/v1/adjustments (T-054 + T-049)
// ────────────────────────────────────────────────────────────────────────────

export const adjustmentsApi = {
  async create(payload: AdjustmentCreate): Promise<AdjustmentRead> {
    await delay();
    // AC-035 / ERR-010 backstop
    if (payload.stock_date > payload.entry_date) {
      throwApiError(422, "stock_date must be on or before entry_date");
    }
    const design = MOCK_DESIGNS.find((d) => d.design_id === payload.design_id);
    if (!design) throwApiError(404, `Design ${payload.design_id} not found`);
    if (!design.is_active)
      throwApiError(422, `Design ${payload.design_id} is inactive`);

    const activePairs = MOCK_DESIGN_GRADE_MAP.filter(
      (m) => m.design_id === payload.design_id && m.is_active
    );
    if (activePairs.length === 0) {
      throwApiError(
        422,
        `Design ${payload.design_id} has no active grade combinations (ERR-012)`
      );
    }
    const activeGradeIds = new Set(activePairs.map((p) => p.grade_id));
    for (const line of payload.lines) {
      if (!activeGradeIds.has(line.grade_id))
        throwApiError(
          422,
          `Grade ${line.grade_id} is not an active mapping for design ${payload.design_id}`
        );
    }

    // Snapshot software_cb + compute difference per line; AC-036/038
    const header_id = nextId(MOCK_ADJUSTMENTS, "header_id");
    const lineRows = payload.lines.map((l, i) => {
      const software_cb = getBalance(payload.design_id, l.grade_id);
      const difference = l.physical_cb - software_cb;
      // AC-039 ledger Δ=difference (skip zero-difference, but keep audit row)
      if (difference !== 0) {
        bumpBalance(payload.design_id, l.grade_id, difference);
      }
      return {
        line_id: i + 1,
        grade_id: l.grade_id,
        software_cb,
        physical_cb: l.physical_cb,
        difference,
      };
    });

    const row: AdjustmentRead = {
      header_id,
      stock_date: payload.stock_date,
      entry_date: payload.entry_date,
      design_id: payload.design_id,
      entered_by_id: payload.entered_by_id,
      created_at: ISO_NOW(),
      lines: lineRows,
    };
    MOCK_ADJUSTMENTS.push(row);
    return row;
  },
};

// ────────────────────────────────────────────────────────────────────────────
// designsTxApi — /api/v1/designs/{id}/grades-with-cb (T-055 + T-050)
// Separate from S1 designsApi to keep S2 endpoints in this file.
// ────────────────────────────────────────────────────────────────────────────

export const designsTxApi = {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async getGradesWithCb(
    designId: number,
    _stockDate: string
  ): Promise<DesignGradeReadWithCb[]> {
    await delay();
    const design = MOCK_DESIGNS.find((d) => d.design_id === designId);
    if (!design) throwApiError(404, `Design ${designId} not found`);
    if (!design.is_active) throwApiError(404, `Design ${designId} not found`); // DS-008 read semantics
    // NOTE: at integration time, _stockDate is sent as ?stock_date= query param;
    // mocks ignore it and use current MOCK_RUNNING_BALANCE (close enough for UI testing).
    return projectGradesWithCb(designId);
  },
};
