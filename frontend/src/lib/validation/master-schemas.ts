// T-030 — Zod schemas mirroring backend Pydantic Create constraints (DS-011).
import { z } from "zod";

export const supplierSchema = z.object({
  supplier_name: z.string().min(1, "Supplier name is required"),
  place: z.string().min(1, "Place is required"),
});

export const staffSchema = z.object({
  staff_name: z.string().min(1, "Staff name is required"),
});

export const dealerSchema = z.object({
  dealer_name: z.string().min(1, "Dealer name is required"),
  place: z.string().min(1, "Place is required"),
});

export const gradeSchema = z.object({
  grade_code: z.string().min(1, "Grade code is required"),
});

export const designSchema = z.object({
  size: z.string().min(1, "Size is required"),
  design_name: z.string().min(1, "Design name is required"),
});

export const designGradeMapSchema = z.object({
  design_id: z
    .number({ required_error: "Please select a design" })
    .int()
    .positive("Please select a design"),
  grade_id: z
    .number({ required_error: "Please select a grade" })
    .int()
    .positive("Please select a grade"),
});

export type SupplierFormValues = z.infer<typeof supplierSchema>;
export type StaffFormValues = z.infer<typeof staffSchema>;
export type DealerFormValues = z.infer<typeof dealerSchema>;
export type GradeFormValues = z.infer<typeof gradeSchema>;
export type DesignFormValues = z.infer<typeof designSchema>;
export type DesignGradeMapFormValues = z.infer<typeof designGradeMapSchema>;
