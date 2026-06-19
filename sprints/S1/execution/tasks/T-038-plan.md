# T-038 — Grades Admin (page + form)

**Module:** M-006 · **Depends on:** T-028, T-030, T-033, T-034 · **TC refs:** TC-043 · **AC:** AC-011, AC-012

## Implementation logic

Mirror of T-035 with substitutions:
- `suppliersApi` -> `gradesApi`
- `Supplier` / `SupplierCreate` -> `Grade` / `GradeCreate`
- `supplierSchema` -> `gradeSchema`
- Columns: `[{key:"grade_id",label:"ID"}, {key:"grade_code",label:"Code"}]`
- Row key: `grade_id`

```tsx
// frontend/src/components/admin/grades/GradeForm.tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { gradeSchema } from "@/lib/validation/master-schemas";
import type { GradeCreate } from "@/types/masters";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Props {
  defaultValues: Partial<GradeCreate>;
  onSubmit: (values: GradeCreate) => void;
  formId: string;
}

export function GradeForm({ defaultValues, onSubmit, formId }: Props) {
  const {
    register, handleSubmit, formState: { errors },
  } = useForm<GradeCreate>({
    resolver: zodResolver(gradeSchema),
    defaultValues: { grade_code: "", ...defaultValues },
  });

  return (
    <form id={formId} onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <div>
        <Label htmlFor="grade_code">Code</Label>
        <Input id="grade_code" {...register("grade_code")} />
        {errors.grade_code && <p className="text-sm text-destructive">{errors.grade_code.message}</p>}
      </div>
    </form>
  );
}
```

Page-level 409 surfacing (already in T-035 onError; works automatically because apiClient interceptor passes `message = detail` to onError):

```ts
const createMut = useMutation({
  mutationFn: gradesApi.create,
  onSuccess: () => { qc.invalidateQueries({ queryKey: QK }); setDialogOpen(false); },
  onError: (e: { status?: number; message?: string }) =>
    toast.error(e?.message ?? "Create failed", { className: "destructive" }),
});
```

## Constraints
- AC-011 surfaces here as toast (variant="destructive") — message must contain "grade_code" (the backend detail)
- DS-011: same form pattern

## Do not touch
Any other file.

## Success criteria
- **Manual:** Create grade with existing code -> red toast "grade_code already exists"
- **Automated:** TC-043 (toast visible + variant destructive + message contains "grade_code")
- **DoD:** Page + form + toast on 409

## Checkout prompt
*"Grades admin — page + form; 409 surfaces as destructive toast (AC-011 client)."*
