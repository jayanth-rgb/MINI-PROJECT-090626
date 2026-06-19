// T-040 — Design-Grade map form (two Select dropdowns wired via Controller).
"use client";

import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  designGradeMapSchema,
  type DesignGradeMapFormValues,
} from "@/lib/validation/master-schemas";
import type { Design, Grade } from "@/types/masters";

interface Props {
  defaultValues: Partial<DesignGradeMapFormValues>;
  designs: Design[];
  grades: Grade[];
  onSubmit: (values: DesignGradeMapFormValues) => void;
  formId: string;
}

export function DesignGradeMapForm({
  defaultValues,
  designs,
  grades,
  onSubmit,
  formId,
}: Props) {
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<DesignGradeMapFormValues>({
    resolver: zodResolver(designGradeMapSchema),
    defaultValues: {
      design_id: defaultValues.design_id ?? 0,
      grade_id: defaultValues.grade_id ?? 0,
    },
  });

  return (
    <form
      id={formId}
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-4"
      noValidate
    >
      <div>
        <Label htmlFor="design_id">Design</Label>
        <Controller
          name="design_id"
          control={control}
          render={({ field }) => (
            <Select
              value={field.value ? String(field.value) : ""}
              onValueChange={(v) => field.onChange(Number(v))}
            >
              <SelectTrigger
                id="design_id"
                data-testid="design-select"
                aria-label="Select a design"
              >
                <SelectValue placeholder="Select a design" />
              </SelectTrigger>
              <SelectContent>
                {designs
                  .filter((d) => d.is_active)
                  .map((d) => (
                    <SelectItem key={d.design_id} value={String(d.design_id)}>
                      {d.design_name} ({d.size})
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          )}
        />
        {errors.design_id && (
          <p className="text-sm text-destructive mt-1">
            {errors.design_id.message}
          </p>
        )}
      </div>
      <div>
        <Label htmlFor="grade_id">Grade</Label>
        <Controller
          name="grade_id"
          control={control}
          render={({ field }) => (
            <Select
              value={field.value ? String(field.value) : ""}
              onValueChange={(v) => field.onChange(Number(v))}
            >
              <SelectTrigger
                id="grade_id"
                data-testid="grade-select"
                aria-label="Select a grade"
              >
                <SelectValue placeholder="Select a grade" />
              </SelectTrigger>
              <SelectContent>
                {grades
                  .filter((g) => g.is_active)
                  .map((g) => (
                    <SelectItem key={g.grade_id} value={String(g.grade_id)}>
                      {g.grade_code}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          )}
        />
        {errors.grade_id && (
          <p className="text-sm text-destructive mt-1">
            {errors.grade_id.message}
          </p>
        )}
      </div>
    </form>
  );
}
