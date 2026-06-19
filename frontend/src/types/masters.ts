// T-026 — TypeScript types mirroring backend Pydantic Read/Create/Update DTOs.

export interface Supplier {
  supplier_id: number;
  supplier_name: string;
  place: string;
  is_active: boolean;
  created_at: string;
}
export interface SupplierCreate {
  supplier_name: string;
  place: string;
}
export interface SupplierUpdate {
  supplier_name?: string;
  place?: string;
  is_active?: boolean;
}

export interface Staff {
  staff_id: number;
  staff_name: string;
  is_active: boolean;
  created_at: string;
}
export interface StaffCreate {
  staff_name: string;
}
export interface StaffUpdate {
  staff_name?: string;
  is_active?: boolean;
}

export interface Dealer {
  dealer_id: number;
  dealer_name: string;
  place: string;
  is_active: boolean;
  created_at: string;
}
export interface DealerCreate {
  dealer_name: string;
  place: string;
}
export interface DealerUpdate {
  dealer_name?: string;
  place?: string;
  is_active?: boolean;
}

export interface Grade {
  grade_id: number;
  grade_code: string;
  is_active: boolean;
}
export interface GradeCreate {
  grade_code: string;
}
export interface GradeUpdate {
  grade_code?: string;
  is_active?: boolean;
}

export interface Design {
  design_id: number;
  size: string;
  design_name: string;
  is_active: boolean;
  created_at: string;
}
export interface DesignCreate {
  size: string;
  design_name: string;
}
export interface DesignUpdate {
  size?: string;
  design_name?: string;
  is_active?: boolean;
}

export interface DesignGradeMap {
  map_id: number;
  design_id: number;
  grade_id: number;
  is_active: boolean;
  design_name?: string;
  grade_code?: string;
}
export interface DesignGradeMapCreate {
  design_id: number;
  grade_id: number;
}
export interface DesignGradeMapUpdate {
  is_active?: boolean;
}

// DF-006 minimal projection — consumed by S2 transaction forms.
export interface DesignGradeMin {
  grade_id: number;
  grade_code: string;
}

// Shared API error contract — matches the live axios interceptor in lib/api/client.ts
// AND the synthetic errors thrown by lib/mocks.ts during the scaffold phase (UR-W004).
export interface ApiError {
  status: number;
  detail: string;
}
