# T-028 — Masters API Wrappers

**Module:** M-006 · **Depends on:** T-026, T-027 · **TC refs:** — · **AC:** AC-019 (contract delivery)

## Implementation logic

```ts
// frontend/src/lib/api/masters.ts
import { apiClient } from "@/lib/api/client";
import type {
  Supplier, SupplierCreate, SupplierUpdate,
  Staff, StaffCreate, StaffUpdate,
  Dealer, DealerCreate, DealerUpdate,
  Grade, GradeCreate, GradeUpdate,
  Design, DesignCreate, DesignUpdate,
  DesignGradeMap, DesignGradeMapCreate, DesignGradeMapUpdate,
  DesignGradeMin,
} from "@/types/masters";

function crud<TRead, TCreate, TUpdate>(path: string) {
  return {
    list: async (includeInactive = false): Promise<TRead[]> =>
      (await apiClient.get<TRead[]>(path, { params: { include_inactive: includeInactive } })).data,
    create: async (payload: TCreate): Promise<TRead> =>
      (await apiClient.post<TRead>(path, payload)).data,
    update: async (id: number, patch: TUpdate): Promise<TRead> =>
      (await apiClient.patch<TRead>(`${path}/${id}`, patch)).data,
    remove: async (id: number): Promise<TRead> =>
      (await apiClient.delete<TRead>(`${path}/${id}`)).data,
  };
}

export const suppliersApi = crud<Supplier, SupplierCreate, SupplierUpdate>("/suppliers");
export const staffApi = crud<Staff, StaffCreate, StaffUpdate>("/staff");
export const dealersApi = crud<Dealer, DealerCreate, DealerUpdate>("/dealers");
export const gradesApi = crud<Grade, GradeCreate, GradeUpdate>("/grades");

export const designsApi = {
  ...crud<Design, DesignCreate, DesignUpdate>("/designs"),
  // DF-006 contract — exposed for S2 transaction forms; S1 admin UI does not call this.
  getGrades: async (design_id: number): Promise<DesignGradeMin[]> =>
    (await apiClient.get<DesignGradeMin[]>(`/designs/${design_id}/grades`)).data,
};

export const designGradeMapApi = crud<DesignGradeMap, DesignGradeMapCreate, DesignGradeMapUpdate>(
  "/design-grade-map"
);
```

## Constraints
- All paths relative to the apiClient baseURL (`NEXT_PUBLIC_API_URL` already points at /api/v1)
- designsApi.getGrades MUST return DesignGradeMin[] exactly (no extra fields)

## Do not touch
Any other file.

## Success criteria
- **Manual:** Import suppliersApi.list; types resolve to Supplier[]
- **Automated:** Indirectly via TC-040/043/045
- **DoD:** 6 entity APIs + designsApi.getGrades

## Checkout prompt
*"Masters API — 6 typed CRUD wrappers + designsApi.getGrades DF-006 hook."*
