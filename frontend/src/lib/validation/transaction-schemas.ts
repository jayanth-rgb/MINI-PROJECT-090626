// S2 — zod schemas for the 3 transaction forms. UX-level validation only;
// backend re-validates via Pydantic (T-046) + DB CHECK constraints (T-044).

import { z } from "zod";

// Helper: today and 7-day window
function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}
function minBackdateISO(): string {
  const d = new Date();
  d.setDate(d.getDate() - 7);
  return d.toISOString().slice(0, 10);
}

// ───────────────────────────────────────────────────────────────────────────
// Inward (F-007 — TC-090..TC-095)
// ───────────────────────────────────────────────────────────────────────────

export const inwardLineCreateSchema = z.object({
  design_id: z.number().int().positive(),
  grade_id: z.number().int().positive(),
  // None/0 = skip per RULE-017; negative rejected per AC-024 / ERR-007.
  nos: z
    .union([z.number().int().nonnegative("nos must be >= 0"), z.null()])
    .nullable()
    .optional(),
});

export const inwardCreateSchema = z
  .object({
    purchase_date: z.string().min(1, "purchase_date is required"),
    supplier_id: z.number().int().positive(),
    entered_by_id: z.number().int().positive(),
    lines: z.array(inwardLineCreateSchema).min(1, "at least one line required"),
  })
  .superRefine((data, ctx) => {
    // AC-020 / ERR-001: future date rejection
    if (data.purchase_date > todayISO()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["purchase_date"],
        message: "purchase_date cannot be in the future",
      });
    }
    // AC-021 / ERR-002: > 7 days prior
    if (data.purchase_date < minBackdateISO()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["purchase_date"],
        message: "purchase_date cannot be older than 7 days",
      });
    }
    // AC-026 / ERR-008: at least one line with nos > 0
    const hasValidLine = data.lines.some(
      (l) => l.nos != null && l.nos > 0
    );
    if (!hasValidLine) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["lines"],
        message: "at least one line with nos > 0 required",
      });
    }
  });

export type InwardFormValues = z.infer<typeof inwardCreateSchema>;

// ───────────────────────────────────────────────────────────────────────────
// Sales (F-008 — TC-096, TC-097)
// ───────────────────────────────────────────────────────────────────────────

export const salesLineCreateSchema = z.object({
  design_id: z.number().int().positive(),
  grade_id: z.number().int().positive(),
  nos: z
    .union([z.number().int().nonnegative("nos must be >= 0"), z.null()])
    .nullable()
    .optional(),
});

export const salesCreateSchema = z
  .object({
    sales_date: z.string().min(1, "sales_date is required"),
    dealer_id: z.number().int().positive(),
    loading_staff_id: z.number().int().positive("loading_staff is required"),
    verified_by_id: z.number().int().positive("verified_by is required"),
    lines: z.array(salesLineCreateSchema).min(1, "at least one line required"),
  })
  .superRefine((data, ctx) => {
    if (data.sales_date > todayISO()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["sales_date"],
        message: "sales_date cannot be in the future",
      });
    }
    if (data.sales_date < minBackdateISO()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["sales_date"],
        message: "sales_date cannot be older than 7 days",
      });
    }
    const hasValidLine = data.lines.some(
      (l) => l.nos != null && l.nos > 0
    );
    if (!hasValidLine) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["lines"],
        message: "at least one line with nos > 0 required",
      });
    }
  });

export type SalesFormValues = z.infer<typeof salesCreateSchema>;

// ───────────────────────────────────────────────────────────────────────────
// Adjustment (F-009 — TC-098..TC-102)
// ───────────────────────────────────────────────────────────────────────────

export const adjustmentLineCreateSchema = z.object({
  grade_id: z.number().int().positive(),
  // AC-037: zero is valid; -1 rejected.
  physical_cb: z.number().int().nonnegative("physical_cb must be >= 0"),
});

export const adjustmentCreateSchema = z
  .object({
    stock_date: z.string().min(1, "stock_date is required"),
    entry_date: z.string().min(1, "entry_date is required"),
    design_id: z.number().int().positive(),
    entered_by_id: z.number().int().positive(),
    lines: z
      .array(adjustmentLineCreateSchema)
      .min(1, "at least one line required"),
  })
  .superRefine((data, ctx) => {
    // AC-035 / ERR-010: cross-field
    if (data.stock_date > data.entry_date) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["entry_date"],
        message: "stock_date must be on or before entry_date",
      });
    }
  });

export type AdjustmentFormValues = z.infer<typeof adjustmentCreateSchema>;
