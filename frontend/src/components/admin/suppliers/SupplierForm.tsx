// T-035 — Supplier form (DS-011 react-hook-form + Zod).
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  supplierSchema,
  type SupplierFormValues,
} from "@/lib/validation/master-schemas";

interface Props {
  defaultValues: Partial<SupplierFormValues>;
  onSubmit: (values: SupplierFormValues) => void;
  formId: string;
}

export function SupplierForm({ defaultValues, onSubmit, formId }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SupplierFormValues>({
    resolver: zodResolver(supplierSchema),
    defaultValues: { supplier_name: "", place: "", ...defaultValues },
  });

  return (
    <form
      id={formId}
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-4"
      noValidate
    >
      <div>
        <Label htmlFor="supplier_name">Supplier Name</Label>
        <Input
          id="supplier_name"
          placeholder="Enter supplier name"
          data-testid="supplier-name-input"
          {...register("supplier_name")}
        />
        {errors.supplier_name && (
          <p className="text-sm text-destructive mt-1">
            {errors.supplier_name.message}
          </p>
        )}
      </div>
      <div>
        <Label htmlFor="place">Place</Label>
        <Input
          id="place"
          placeholder="Enter place"
          data-testid="supplier-place-input"
          {...register("place")}
        />
        {errors.place && (
          <p className="text-sm text-destructive mt-1">
            {errors.place.message}
          </p>
        )}
      </div>
    </form>
  );
}
