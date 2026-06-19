// T-036 — Staff form.
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { staffSchema, type StaffFormValues } from "@/lib/validation/master-schemas";

interface Props {
  defaultValues: Partial<StaffFormValues>;
  onSubmit: (values: StaffFormValues) => void;
  formId: string;
}

export function StaffForm({ defaultValues, onSubmit, formId }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<StaffFormValues>({
    resolver: zodResolver(staffSchema),
    defaultValues: { staff_name: "", ...defaultValues },
  });

  return (
    <form
      id={formId}
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-4"
      noValidate
    >
      <div>
        <Label htmlFor="staff_name">Staff Name</Label>
        <Input
          id="staff_name"
          placeholder="Enter staff name"
          data-testid="staff-name-input"
          {...register("staff_name")}
        />
        {errors.staff_name && (
          <p className="text-sm text-destructive mt-1">
            {errors.staff_name.message}
          </p>
        )}
      </div>
    </form>
  );
}
