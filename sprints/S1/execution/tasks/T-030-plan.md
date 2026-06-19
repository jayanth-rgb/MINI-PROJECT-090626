# T-030 — Zod Schemas

**Module:** M-006 · **Depends on:** — · **TC refs:** — · **AC:** AC-001/004/007/010/013/016 (client-side enforcement)

## Implementation logic

```ts
// frontend/src/lib/validation/master-schemas.ts
import { z } from "zod";

export const supplierSchema = z.object({
  supplier_name: z.string().min(1, "supplier_name required"),
  place: z.string().min(1, "place required"),
});

export const staffSchema = z.object({
  staff_name: z.string().min(1, "staff_name required"),
});

export const dealerSchema = z.object({
  dealer_name: z.string().min(1, "dealer_name required"),
  place: z.string().min(1, "place required"),
});

export const gradeSchema = z.object({
  grade_code: z.string().min(1, "grade_code required"),
});

export const designSchema = z.object({
  size: z.string().min(1, "size required"),
  design_name: z.string().min(1, "design_name required"),
});

export const designGradeMapSchema = z.object({
  design_id: z.number().int().positive("design_id required"),
  grade_id: z.number().int().positive("grade_id required"),
});
```

## Constraints
- DS-011: forms use zodResolver — schemas live here, NOT inside form components
- Mirror Pydantic Create exactly (min_length=1 on names; positive int on FK fields)

## Do not touch
Any other file.

## Success criteria
- **Manual:** `supplierSchema.safeParse({supplier_name:'', place:'X'})` -> `success: false`
- **Automated:** TC-039, TC-041, TC-042, TC-044, TC-046 verify the resolver blocks invalid submits
- **DoD:** 6 schemas exported

## Checkout prompt
*"Zod schemas — 6 admin form validators mirroring Pydantic."*
