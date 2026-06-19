// T-037 — Dealer form.
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { dealerSchema, type DealerFormValues } from "@/lib/validation/master-schemas";

interface Props {
  defaultValues: Partial<DealerFormValues>;
  onSubmit: (values: DealerFormValues) => void;
  formId: string;
}

export function DealerForm({ defaultValues, onSubmit, formId }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<DealerFormValues>({
    resolver: zodResolver(dealerSchema),
    defaultValues: { dealer_name: "", place: "", ...defaultValues },
  });

  return (
    <form
      id={formId}
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-4"
      noValidate
    >
      <div>
        <Label htmlFor="dealer_name">Dealer Name</Label>
        <Input
          id="dealer_name"
          placeholder="Enter dealer name"
          data-testid="dealer-name-input"
          {...register("dealer_name")}
        />
        {errors.dealer_name && (
          <p className="text-sm text-destructive mt-1">
            {errors.dealer_name.message}
          </p>
        )}
      </div>
      <div>
        <Label htmlFor="place">Place</Label>
        <Input
          id="place"
          placeholder="Enter place"
          data-testid="dealer-place-input"
          {...register("place")}
        />
        {errors.place && (
          <p className="text-sm text-destructive mt-1">{errors.place.message}</p>
        )}
      </div>
    </form>
  );
}
