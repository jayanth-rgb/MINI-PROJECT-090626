# T-039 — Designs Admin (page + form)

**Module:** M-006 · **Depends on:** T-028, T-030, T-033, T-034 · **TC refs:** TC-044 · **AC:** AC-013, AC-015

## Implementation logic

Mirror of T-035 with substitutions:
- `suppliersApi` -> `designsApi`
- `Supplier` / `SupplierCreate` -> `Design` / `DesignCreate`
- `supplierSchema` -> `designSchema`
- Columns: `[{key:"design_id",label:"ID"}, {key:"size",label:"Size"}, {key:"design_name",label:"Name"}]`
- Row key: `design_id`

```tsx
// frontend/src/components/admin/designs/DesignForm.tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { designSchema } from "@/lib/validation/master-schemas";
import type { DesignCreate } from "@/types/masters";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Props {
  defaultValues: Partial<DesignCreate>;
  onSubmit: (values: DesignCreate) => void;
  formId: string;
}

export function DesignForm({ defaultValues, onSubmit, formId }: Props) {
  const {
    register, handleSubmit, formState: { errors },
  } = useForm<DesignCreate>({
    resolver: zodResolver(designSchema),
    defaultValues: { size: "", design_name: "", ...defaultValues },
  });

  return (
    <form id={formId} onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <div>
        <Label htmlFor="size">Size</Label>
        <Input id="size" {...register("size")} />
        {errors.size && <p className="text-sm text-destructive">{errors.size.message}</p>}
      </div>
      <div>
        <Label htmlFor="design_name">Name</Label>
        <Input id="design_name" {...register("design_name")} />
        {errors.design_name && <p className="text-sm text-destructive">{errors.design_name.message}</p>}
      </div>
    </form>
  );
}
```

## Constraints
- DS-011: same form pattern as T-035
- Note: designsApi.getGrades is exposed but NOT used by the S1 admin UI

## Do not touch
Any other file.

## Success criteria
- **Manual:** /admin/designs CRUD works
- **Automated:** TC-044 (parameterised empty)
- **DoD:** Page + form rendered

## Checkout prompt
*"Designs admin — page + form. AC-013 + AC-015."*
