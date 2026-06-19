// T-028 — Integration boundary. The ONLY file Sonnet rewrites during
// /ases-dev to swap mock-backed calls for real backend calls. Every UI
// component/hook imports from this module; nothing imports from mocks.ts
// directly.
//
// Scaffold phase: each function calls helpers in @/lib/mocks. Latency simulated
// via delay() so React Query loading states render naturally.
// Integration phase: Sonnet replaces the bodies with apiClient.get/post/...
// calls and deletes mocks.ts.

import type {
  Supplier,
  SupplierCreate,
  SupplierUpdate,
  Staff,
  StaffCreate,
  StaffUpdate,
  Dealer,
  DealerCreate,
  DealerUpdate,
  Grade,
  GradeCreate,
  GradeUpdate,
  Design,
  DesignCreate,
  DesignUpdate,
  DesignGradeMap,
  DesignGradeMapCreate,
  DesignGradeMapUpdate,
  DesignGradeMin,
} from "@/types/masters";
import {
  MOCK_SUPPLIERS,
  MOCK_STAFF,
  MOCK_DEALERS,
  MOCK_GRADES,
  MOCK_DESIGNS,
  MOCK_DESIGN_GRADE_MAP,
  delay,
  hydrateMapRow,
  nextId,
  throwApiError,
} from "@/lib/mocks";

const ISO_NOW = () => new Date().toISOString();

// ============================================================================
// suppliersApi — /api/v1/suppliers
// ============================================================================

export const suppliersApi = {
  async list(includeInactive = false): Promise<Supplier[]> {
    await delay();
    return includeInactive ? [...MOCK_SUPPLIERS] : MOCK_SUPPLIERS.filter((r) => r.is_active);
  },
  async create(payload: SupplierCreate): Promise<Supplier> {
    await delay();
    const row: Supplier = {
      supplier_id: nextId(MOCK_SUPPLIERS, "supplier_id"),
      supplier_name: payload.supplier_name,
      place: payload.place,
      is_active: true,
      created_at: ISO_NOW(),
    };
    MOCK_SUPPLIERS.push(row);
    return row;
  },
  async update(id: number, patch: SupplierUpdate): Promise<Supplier> {
    await delay();
    const i = MOCK_SUPPLIERS.findIndex((r) => r.supplier_id === id);
    if (i === -1) throwApiError(404, `Supplier ${id} not found`);
    const updated = { ...MOCK_SUPPLIERS[i], ...patch };
    MOCK_SUPPLIERS[i] = updated;
    return updated;
  },
  async remove(id: number): Promise<Supplier> {
    await delay();
    const i = MOCK_SUPPLIERS.findIndex((r) => r.supplier_id === id);
    if (i === -1) throwApiError(404, `Supplier ${id} not found`);
    MOCK_SUPPLIERS[i] = { ...MOCK_SUPPLIERS[i], is_active: false };
    return MOCK_SUPPLIERS[i];
  },
};

// ============================================================================
// staffApi — /api/v1/staff
// ============================================================================

export const staffApi = {
  async list(includeInactive = false): Promise<Staff[]> {
    await delay();
    return includeInactive ? [...MOCK_STAFF] : MOCK_STAFF.filter((r) => r.is_active);
  },
  async create(payload: StaffCreate): Promise<Staff> {
    await delay();
    const row: Staff = {
      staff_id: nextId(MOCK_STAFF, "staff_id"),
      staff_name: payload.staff_name,
      is_active: true,
      created_at: ISO_NOW(),
    };
    MOCK_STAFF.push(row);
    return row;
  },
  async update(id: number, patch: StaffUpdate): Promise<Staff> {
    await delay();
    const i = MOCK_STAFF.findIndex((r) => r.staff_id === id);
    if (i === -1) throwApiError(404, `Staff ${id} not found`);
    const updated = { ...MOCK_STAFF[i], ...patch };
    MOCK_STAFF[i] = updated;
    return updated;
  },
  async remove(id: number): Promise<Staff> {
    await delay();
    const i = MOCK_STAFF.findIndex((r) => r.staff_id === id);
    if (i === -1) throwApiError(404, `Staff ${id} not found`);
    MOCK_STAFF[i] = { ...MOCK_STAFF[i], is_active: false };
    return MOCK_STAFF[i];
  },
};

// ============================================================================
// dealersApi — /api/v1/dealers
// ============================================================================

export const dealersApi = {
  async list(includeInactive = false): Promise<Dealer[]> {
    await delay();
    return includeInactive ? [...MOCK_DEALERS] : MOCK_DEALERS.filter((r) => r.is_active);
  },
  async create(payload: DealerCreate): Promise<Dealer> {
    await delay();
    const row: Dealer = {
      dealer_id: nextId(MOCK_DEALERS, "dealer_id"),
      dealer_name: payload.dealer_name,
      place: payload.place,
      is_active: true,
      created_at: ISO_NOW(),
    };
    MOCK_DEALERS.push(row);
    return row;
  },
  async update(id: number, patch: DealerUpdate): Promise<Dealer> {
    await delay();
    const i = MOCK_DEALERS.findIndex((r) => r.dealer_id === id);
    if (i === -1) throwApiError(404, `Dealer ${id} not found`);
    const updated = { ...MOCK_DEALERS[i], ...patch };
    MOCK_DEALERS[i] = updated;
    return updated;
  },
  async remove(id: number): Promise<Dealer> {
    await delay();
    const i = MOCK_DEALERS.findIndex((r) => r.dealer_id === id);
    if (i === -1) throwApiError(404, `Dealer ${id} not found`);
    MOCK_DEALERS[i] = { ...MOCK_DEALERS[i], is_active: false };
    return MOCK_DEALERS[i];
  },
};

// ============================================================================
// gradesApi — /api/v1/grades (AC-011 UNIQUE grade_code)
// ============================================================================

export const gradesApi = {
  async list(includeInactive = false): Promise<Grade[]> {
    await delay();
    return includeInactive ? [...MOCK_GRADES] : MOCK_GRADES.filter((r) => r.is_active);
  },
  async create(payload: GradeCreate): Promise<Grade> {
    await delay();
    if (MOCK_GRADES.some((g) => g.grade_code === payload.grade_code)) {
      throwApiError(409, `grade_code '${payload.grade_code}' already exists`);
    }
    const row: Grade = {
      grade_id: nextId(MOCK_GRADES, "grade_id"),
      grade_code: payload.grade_code,
      is_active: true,
    };
    MOCK_GRADES.push(row);
    return row;
  },
  async update(id: number, patch: GradeUpdate): Promise<Grade> {
    await delay();
    const i = MOCK_GRADES.findIndex((r) => r.grade_id === id);
    if (i === -1) throwApiError(404, `Grade ${id} not found`);
    if (
      patch.grade_code &&
      MOCK_GRADES.some((g) => g.grade_code === patch.grade_code && g.grade_id !== id)
    ) {
      throwApiError(409, `grade_code '${patch.grade_code}' already exists`);
    }
    const updated = { ...MOCK_GRADES[i], ...patch };
    MOCK_GRADES[i] = updated;
    return updated;
  },
  async remove(id: number): Promise<Grade> {
    await delay();
    const i = MOCK_GRADES.findIndex((r) => r.grade_id === id);
    if (i === -1) throwApiError(404, `Grade ${id} not found`);
    MOCK_GRADES[i] = { ...MOCK_GRADES[i], is_active: false };
    return MOCK_GRADES[i];
  },
};

// ============================================================================
// designsApi — /api/v1/designs + /api/v1/designs/{id}/grades (DF-006 contract)
// ============================================================================

export const designsApi = {
  async list(includeInactive = false): Promise<Design[]> {
    await delay();
    return includeInactive ? [...MOCK_DESIGNS] : MOCK_DESIGNS.filter((r) => r.is_active);
  },
  async create(payload: DesignCreate): Promise<Design> {
    await delay();
    const row: Design = {
      design_id: nextId(MOCK_DESIGNS, "design_id"),
      size: payload.size,
      design_name: payload.design_name,
      is_active: true,
      created_at: ISO_NOW(),
    };
    MOCK_DESIGNS.push(row);
    return row;
  },
  async update(id: number, patch: DesignUpdate): Promise<Design> {
    await delay();
    const i = MOCK_DESIGNS.findIndex((r) => r.design_id === id);
    if (i === -1) throwApiError(404, `Design ${id} not found`);
    const updated = { ...MOCK_DESIGNS[i], ...patch };
    MOCK_DESIGNS[i] = updated;
    return updated;
  },
  async remove(id: number): Promise<Design> {
    await delay();
    const i = MOCK_DESIGNS.findIndex((r) => r.design_id === id);
    if (i === -1) throwApiError(404, `Design ${id} not found`);
    MOCK_DESIGNS[i] = { ...MOCK_DESIGNS[i], is_active: false };
    return MOCK_DESIGNS[i];
  },
  // DF-006 contract exposed for S2 transaction forms. AC-019.
  async getGrades(designId: number): Promise<DesignGradeMin[]> {
    await delay();
    return MOCK_DESIGN_GRADE_MAP
      .filter((m) => m.design_id === designId && m.is_active)
      .map((m) => {
        const grade = MOCK_GRADES.find((g) => g.grade_id === m.grade_id && g.is_active);
        return grade ? { grade_id: grade.grade_id, grade_code: grade.grade_code } : null;
      })
      .filter((r): r is DesignGradeMin => r !== null);
  },
};

// ============================================================================
// designGradeMapApi — /api/v1/design-grade-map (AC-016 UNIQUE pair)
// ============================================================================

export const designGradeMapApi = {
  async list(includeInactive = false): Promise<DesignGradeMap[]> {
    await delay();
    const rows = includeInactive
      ? [...MOCK_DESIGN_GRADE_MAP]
      : MOCK_DESIGN_GRADE_MAP.filter((r) => r.is_active);
    return rows.map(hydrateMapRow);
  },
  async create(payload: DesignGradeMapCreate): Promise<DesignGradeMap> {
    await delay();
    if (!MOCK_DESIGNS.some((d) => d.design_id === payload.design_id)) {
      throwApiError(404, `Design ${payload.design_id} not found`);
    }
    if (!MOCK_GRADES.some((g) => g.grade_id === payload.grade_id)) {
      throwApiError(404, `Grade ${payload.grade_id} not found`);
    }
    if (
      MOCK_DESIGN_GRADE_MAP.some(
        (m) => m.design_id === payload.design_id && m.grade_id === payload.grade_id
      )
    ) {
      throwApiError(
        409,
        `(design_id, grade_id) = (${payload.design_id}, ${payload.grade_id}) already exists`
      );
    }
    const row: DesignGradeMap = {
      map_id: nextId(MOCK_DESIGN_GRADE_MAP, "map_id"),
      design_id: payload.design_id,
      grade_id: payload.grade_id,
      is_active: true,
    };
    MOCK_DESIGN_GRADE_MAP.push(row);
    return hydrateMapRow(row);
  },
  async update(id: number, patch: DesignGradeMapUpdate): Promise<DesignGradeMap> {
    await delay();
    const i = MOCK_DESIGN_GRADE_MAP.findIndex((r) => r.map_id === id);
    if (i === -1) throwApiError(404, `Mapping ${id} not found`);
    MOCK_DESIGN_GRADE_MAP[i] = { ...MOCK_DESIGN_GRADE_MAP[i], ...patch };
    return hydrateMapRow(MOCK_DESIGN_GRADE_MAP[i]);
  },
  async remove(id: number): Promise<DesignGradeMap> {
    await delay();
    const i = MOCK_DESIGN_GRADE_MAP.findIndex((r) => r.map_id === id);
    if (i === -1) throwApiError(404, `Mapping ${id} not found`);
    MOCK_DESIGN_GRADE_MAP[i] = { ...MOCK_DESIGN_GRADE_MAP[i], is_active: false };
    return hydrateMapRow(MOCK_DESIGN_GRADE_MAP[i]);
  },
};
