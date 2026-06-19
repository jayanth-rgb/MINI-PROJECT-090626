// T-038 — Grade form.
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { gradeSchema, type GradeFormValues } from "@/lib/validation/master-schemas";

interface Props {
  defaultValues: Partial<GradeFormValues>;
  onSubmit: (values: GradeFormValues) => void;
  formId: string;
}

export function GradeForm({ defaultValues, onSubmit, formId }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<GradeFormValues>({
    resolver: zodResolver(gradeSchema),
    defaultValues: { grade_code: "", ...defaultValues },
  });

  return (
    <form
      id={formId}
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-4"
      noValidate
    >
      <div>
        <Label htmlFor="grade_code">Grade Code</Label>
        <Input
          id="grade_code"
          placeholder="Enter grade code (e.g. 1, 2A, OB)"
          data-testid="grade-code-input"
          {...register("grade_code")}
        />
        {errors.grade_code && (
          <p className="text-sm text-destructive mt-1">
            {errors.grade_code.message}
          </p>
        )}
      </div>
    </form>
  );
}
