// T-039 — Design form.
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { designSchema, type DesignFormValues } from "@/lib/validation/master-schemas";

interface Props {
  defaultValues: Partial<DesignFormValues>;
  onSubmit: (values: DesignFormValues) => void;
  formId: string;
}

export function DesignForm({ defaultValues, onSubmit, formId }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<DesignFormValues>({
    resolver: zodResolver(designSchema),
    defaultValues: { size: "", design_name: "", ...defaultValues },
  });

  return (
    <form
      id={formId}
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-4"
      noValidate
    >
      <div>
        <Label htmlFor="size">Size</Label>
        <Input
          id="size"
          placeholder="Enter size (e.g. 16X10)"
          data-testid="design-size-input"
          {...register("size")}
        />
        {errors.size && (
          <p className="text-sm text-destructive mt-1">{errors.size.message}</p>
        )}
      </div>
      <div>
        <Label htmlFor="design_name">Design Name</Label>
        <Input
          id="design_name"
          placeholder="Enter design name"
          data-testid="design-name-input"
          {...register("design_name")}
        />
        {errors.design_name && (
          <p className="text-sm text-destructive mt-1">
            {errors.design_name.message}
          </p>
        )}
      </div>
    </form>
  );
}
