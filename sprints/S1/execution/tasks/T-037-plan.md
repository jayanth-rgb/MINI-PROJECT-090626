# T-037 — Dealers Admin (page + form)

**Module:** M-006 · **Depends on:** T-028, T-030, T-033, T-034 · **TC refs:** TC-042 · **AC:** AC-007, AC-008

## Implementation logic

Mirror of T-035 with substitutions:
- `suppliersApi` -> `dealersApi`
- `Supplier` / `SupplierCreate` -> `Dealer` / `DealerCreate`
- `supplierSchema` -> `dealerSchema`
- Columns: `[{key:"dealer_id",label:"ID"}, {key:"dealer_name",label:"Name"}, {key:"place",label:"Place"}]`
- Row key: `dealer_id`

```tsx
// frontend/src/components/admin/dealers/DealerForm.tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { dealerSchema } from "@/lib/validation/master-schemas";
import type { DealerCreate } from "@/types/masters";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Props {
  defaultValues: Partial<DealerCreate>;
  onSubmit: (values: DealerCreate) => void;
  formId: string;
}

export function DealerForm({ defaultValues, onSubmit, formId }: Props) {
  const {
    register, handleSubmit, formState: { errors },
  } = useForm<DealerCreate>({
    resolver: zodResolver(dealerSchema),
    defaultValues: { dealer_name: "", place: "", ...defaultValues },
  });

  return (
    <form id={formId} onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <div>
        <Label htmlFor="dealer_name">Name</Label>
        <Input id="dealer_name" {...register("dealer_name")} />
        {errors.dealer_name && <p className="text-sm text-destructive">{errors.dealer_name.message}</p>}
      </div>
      <div>
        <Label htmlFor="place">Place</Label>
        <Input id="place" {...register("place")} />
        {errors.place && <p className="text-sm text-destructive">{errors.place.message}</p>}
      </div>
    </form>
  );
}
```

## Constraints
- DS-011: same pattern as T-035

## Do not touch
Any other file.

## Success criteria
- **Manual:** /admin/dealers loads with 3 seeded dealers; CRUD works
- **Automated:** TC-042 (both empty variants block onSubmit)
- **DoD:** Page + form rendered

## Checkout prompt
*"Dealers admin — page + form. AC-007 + AC-008."*
