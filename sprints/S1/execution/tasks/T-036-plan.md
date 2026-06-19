# T-036 — Staff Admin (page + form)

**Module:** M-006 · **Depends on:** T-028, T-030, T-033, T-034 · **TC refs:** TC-041 · **AC:** AC-004, AC-005

## Implementation logic

Mirror of T-035 with these substitutions:
- `suppliersApi` → `staffApi`
- `Supplier` / `SupplierCreate` → `Staff` / `StaffCreate`
- `supplierSchema` → `staffSchema`
- Page columns: `[{key:"staff_id",label:"ID"}, {key:"staff_name",label:"Name"}]`
- Form has a single field: `staff_name`

```tsx
// frontend/src/components/admin/staff/StaffForm.tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { staffSchema } from "@/lib/validation/master-schemas";
import type { StaffCreate } from "@/types/masters";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Props {
  defaultValues: Partial<StaffCreate>;
  onSubmit: (values: StaffCreate) => void;
  formId: string;
}

export function StaffForm({ defaultValues, onSubmit, formId }: Props) {
  const {
    register, handleSubmit, formState: { errors },
  } = useForm<StaffCreate>({
    resolver: zodResolver(staffSchema),
    defaultValues: { staff_name: "", ...defaultValues },
  });

  return (
    <form id={formId} onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <div>
        <Label htmlFor="staff_name">Name</Label>
        <Input id="staff_name" {...register("staff_name")} />
        {errors.staff_name && <p className="text-sm text-destructive">{errors.staff_name.message}</p>}
      </div>
    </form>
  );
}
```

Page is structurally identical to SuppliersPage — only the API + types + columns + form change.

## Constraints
- DS-011: same form pattern as T-035
- Row key: `staff_id`

## Do not touch
Any other file.

## Success criteria
- **Manual:** /admin/staff loads with seeded 9 names; CRUD works
- **Automated:** TC-041 (empty staff_name blocks)
- **DoD:** Page + form rendered

## Checkout prompt
*"Staff admin — page + form. AC-004 + AC-005."*
