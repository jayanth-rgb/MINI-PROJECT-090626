"use client";

import { useEffect, useState } from "react";
import { useForm, useFieldArray, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DatePicker } from "@/components/ui/date-picker";
import { TransactionLineRow } from "@/components/transactions/shared/TransactionLineRow";

import { suppliersApi, staffApi, designsApi } from "@/lib/api/masters";
import { inwardApi } from "@/lib/api/transactions";
import {
  inwardCreateSchema,
  type InwardFormValues,
} from "@/lib/validation/transaction-schemas";
import type { InwardCreate } from "@/types/transactions";
import type { ApiError } from "@/types/masters";

export function InwardForm() {
  const router = useRouter();
  const [designId, setDesignId] = useState<number | undefined>(undefined);

  const suppliersQ = useQuery({
    queryKey: ["suppliers"],
    queryFn: () => suppliersApi.list(),
  });
  const staffQ = useQuery({
    queryKey: ["staff"],
    queryFn: () => staffApi.list(),
  });
  const designsQ = useQuery({
    queryKey: ["designs"],
    queryFn: () => designsApi.list(),
  });
  const gradesQ = useQuery({
    queryKey: ["designs", designId, "grades"],
    queryFn: () => designsApi.getGrades(designId!),
    enabled: !!designId,
  });

  const form = useForm<InwardFormValues>({
    resolver: zodResolver(inwardCreateSchema),
    defaultValues: {
      purchase_date: new Date().toISOString().slice(0, 10),
      supplier_id: 0,
      entered_by_id: 0,
      lines: [],
    },
    mode: "onSubmit",
  });
  const { fields, replace } = useFieldArray({
    control: form.control,
    name: "lines",
  });

  // Reactively replace line rows when grades data arrives (UR-W008 pattern).
  useEffect(() => {
    if (!designId || !gradesQ.data) return;
    replace(
      gradesQ.data.map((g) => ({
        design_id: designId,
        grade_id: g.grade_id,
        nos: null,
      }))
    );
  }, [designId, gradesQ.data, replace]);

  const supplierId = form.watch("supplier_id");
  const selectedSupplier = suppliersQ.data?.find(
    (s) => s.supplier_id === Number(supplierId)
  );

  const mutation = useMutation({
    mutationFn: (payload: InwardCreate) => inwardApi.create(payload),
    onSuccess: () => {
      toast.success("Inward saved");
      form.reset();
      setDesignId(undefined);
      router.refresh();
    },
    onError: (err: ApiError) => {
      toast.error(err.detail ?? "Save failed");
    },
  });

  const onSubmit = (values: InwardFormValues) => {
    const lines = values.lines
      .filter((l) => l.nos != null && l.nos > 0)
      .map((l) => ({
        design_id: l.design_id,
        grade_id: l.grade_id,
        nos: l.nos as number,
      }));

    mutation.mutate({
      purchase_date: values.purchase_date,
      supplier_id: values.supplier_id,
      entered_by_id: values.entered_by_id,
      lines,
    });
  };

  const linesError = form.formState.errors.lines?.message as string | undefined;

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>New Inward</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          {/* Purchase date */}
          <div className="space-y-1.5">
            <Label htmlFor="purchase_date">Purchase date</Label>
            <Controller
              control={form.control}
              name="purchase_date"
              render={({ field, fieldState }) => (
                <DatePicker
                  id="purchase_date"
                  value={field.value}
                  onChange={(iso) => field.onChange(iso ?? "")}
                  ariaInvalid={!!fieldState.error}
                  ariaDescribedBy={
                    fieldState.error ? "purchase_date-error" : undefined
                  }
                />
              )}
            />
            {form.formState.errors.purchase_date && (
              <p id="purchase_date-error" role="alert" className="text-xs text-destructive">
                {form.formState.errors.purchase_date.message}
              </p>
            )}
          </div>

          {/* Supplier */}
          <div className="space-y-1.5">
            <Label htmlFor="supplier_id">Supplier</Label>
            <Controller
              control={form.control}
              name="supplier_id"
              render={({ field }) => (
                <Select
                  value={field.value ? String(field.value) : ""}
                  onValueChange={(v) => field.onChange(Number(v))}
                >
                  <SelectTrigger id="supplier_id" aria-required="true">
                    <SelectValue placeholder="Select supplier" />
                  </SelectTrigger>
                  <SelectContent>
                    {suppliersQ.data?.map((s) => (
                      <SelectItem key={s.supplier_id} value={String(s.supplier_id)}>
                        {s.supplier_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {form.formState.errors.supplier_id && (
              <p role="alert" className="text-xs text-destructive">
                {form.formState.errors.supplier_id.message}
              </p>
            )}
          </div>

          {/* Place (read-only mirror of supplier.place per DS-013 / AC-022) */}
          <div className="space-y-1.5">
            <Label htmlFor="place">Place</Label>
            <Input
              id="place"
              data-testid="inward-place"
              value={selectedSupplier?.place ?? ""}
              readOnly
              placeholder="Auto-filled from supplier"
              className="bg-muted"
            />
          </div>

          {/* Entered by */}
          <div className="space-y-1.5">
            <Label htmlFor="entered_by_id">Entered by</Label>
            <Controller
              control={form.control}
              name="entered_by_id"
              render={({ field }) => (
                <Select
                  value={field.value ? String(field.value) : ""}
                  onValueChange={(v) => field.onChange(Number(v))}
                >
                  <SelectTrigger id="entered_by_id" aria-required="true">
                    <SelectValue placeholder="Select staff" />
                  </SelectTrigger>
                  <SelectContent>
                    {staffQ.data?.map((s) => (
                      <SelectItem key={s.staff_id} value={String(s.staff_id)}>
                        {s.staff_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {form.formState.errors.entered_by_id && (
              <p role="alert" className="text-xs text-destructive">
                {form.formState.errors.entered_by_id.message}
              </p>
            )}
          </div>

          {/* Design (UI-only — drives line rows) */}
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="design_id">Design</Label>
            <Select
              value={designId ? String(designId) : ""}
              onValueChange={(v) => setDesignId(Number(v))}
            >
              <SelectTrigger id="design_id" aria-required="true">
                <SelectValue placeholder="Select design" />
              </SelectTrigger>
              <SelectContent>
                {designsQ.data?.map((d) => (
                  <SelectItem key={d.design_id} value={String(d.design_id)}>
                    {d.design_name} ({d.size})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {fields.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Grades</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {fields.map((field, index) => (
              <Controller
                key={field.id}
                control={form.control}
                name={`lines.${index}.nos`}
                render={({ field: nosField, fieldState }) => (
                  <TransactionLineRow
                    index={index}
                    gradeCode={gradesQ.data?.[index]?.grade_code ?? ""}
                    value={nosField.value}
                    onChange={nosField.onChange}
                    errorId={`line-${index}-nos-error`}
                    errorMessage={fieldState.error?.message}
                  />
                )}
              />
            ))}
            {linesError && (
              <p role="alert" className="text-sm text-destructive">
                {linesError}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      <div className="flex justify-end">
        <Button
          type="submit"
          disabled={mutation.isPending}
          aria-busy={mutation.isPending}
        >
          {mutation.isPending ? "Saving..." : "Save Inward"}
        </Button>
      </div>
    </form>
  );
}
