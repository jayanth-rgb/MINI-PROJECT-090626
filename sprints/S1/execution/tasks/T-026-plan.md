# T-026 — TypeScript Types (masters.ts)

**Module:** M-006 · **Depends on:** — · **TC refs:** — · **AC:** —

## Implementation logic

```ts
// frontend/src/types/masters.ts

export interface Supplier {
  supplier_id: number;
  supplier_name: string;
  place: string;
  is_active: boolean;
  created_at: string;
}
export interface SupplierCreate { supplier_name: string; place: string; }
export interface SupplierUpdate { supplier_name?: string; place?: string; is_active?: boolean; }

export interface Staff {
  staff_id: number;
  staff_name: string;
  is_active: boolean;
  created_at: string;
}
export interface StaffCreate { staff_name: string; }
export interface StaffUpdate { staff_name?: string; is_active?: boolean; }

export interface Dealer {
  dealer_id: number;
  dealer_name: string;
  place: string;
  is_active: boolean;
  created_at: string;
}
export interface DealerCreate { dealer_name: string; place: string; }
export interface DealerUpdate { dealer_name?: string; place?: string; is_active?: boolean; }

export interface Grade {
  grade_id: number;
  grade_code: string;
  is_active: boolean;
}
export interface GradeCreate { grade_code: string; }
export interface GradeUpdate { grade_code?: string; is_active?: boolean; }

export interface Design {
  design_id: number;
  size: string;
  design_name: string;
  is_active: boolean;
  created_at: string;
}
export interface DesignCreate { size: string; design_name: string; }
export interface DesignUpdate { size?: string; design_name?: string; is_active?: boolean; }

export interface DesignGradeMap {
  map_id: number;
  design_id: number;
  grade_id: number;
  is_active: boolean;
  design_name?: string;
  grade_code?: string;
}
export interface DesignGradeMapCreate { design_id: number; grade_id: number; }
export interface DesignGradeMapUpdate { is_active?: boolean; }

export interface DesignGradeMin { grade_id: number; grade_code: string; }
```

## Constraints
- Field names and types must mirror backend Pydantic Read schemas exactly
- DesignGradeMin used for GET /designs/{id}/grades (DF-006 contract)

## Do not touch
Any other file.

## Success criteria
- **Manual:** `npx tsc --noEmit` passes after import in masters.ts API wrapper
- **Automated:** Compile-checked
- **DoD:** All Read/Create/Update + DesignGradeMin exported

## Checkout prompt
*"TS types for 6 entities + DesignGradeMin — mirrors backend."*
