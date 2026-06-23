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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DatePicker } from "@/components/ui/date-picker";
import { AdjustmentLineRow } from "@/components/transactions/adjustment/AdjustmentLineRow";
import { Err012Banner } from "@/components/transactions/adjustment/Err012Banner";

import { staffApi, designsApi } from "@/lib/api/masters";
import { adjustmentsApi, designsTxApi } from "@/lib/api/transactions";
import {
  adjustmentCreateSchema,
  type AdjustmentFormValues,
} from "@/lib/validation/transaction-schemas";
import type { AdjustmentCreate } from "@/types/transactions";
import type { ApiError } from "@/types/masters";

export function AdjustmentForm() {
  const router = useRouter();
  const [designId, setDesignId] = useState<number | undefined>(undefined);
  const [stockDate, setStockDate] = useState<string>(
    new Date().toISOString().slice(0, 10)
  );

  const staffQ = useQuery({
    queryKey: ["staff"],
    queryFn: () => staffApi.list(),
  });
  const designsQ = useQuery({
    queryKey: ["designs"],
    queryFn: () => designsApi.list(),
  });
  const gradesWithCbQ = useQuery({
    queryKey: ["designs", designId, "grades-with-cb", stockDate],
    queryFn: () => designsTxApi.getGradesWithCb(designId!, stockDate),
    enabled: !!designId && !!stockDate,
  });

  const form = useForm<AdjustmentFormValues>({
    resolver: zodResolver(adjustmentCreateSchema),
    defaultValues: {
      stock_date: stockDate,
      entry_date: new Date().toISOString().slice(0, 10),
      design_id: 0,
      entered_by_id: 0,
      lines: [],
    },
    mode: "onSubmit",
  });
  const { fields, replace } = useFieldArray({
    control: form.control,
    name: "lines",
  });

  // UR-W008: reactive sync of line rows whenever query data changes.
  useEffect(() => {
    if (gradesWithCbQ.data === undefined) return;
    replace(
      gradesWithCbQ.data.map((g) => ({
        grade_id: g.grade_id,
        physical_cb: 0,
      }))
    );
  }, [gradesWithCbQ.data, replace]);

  const selectedDesign = designsQ.data?.find((d) => d.design_id === designId);
  const showErr012 =
    !!designId && gradesWithCbQ.isSuccess && gradesWithCbQ.data!.length === 0;

  const mutation = useMutation({
    mutationFn: (payload: AdjustmentCreate) => adjustmentsApi.create(payload),
    onSuccess: () => {
      toast.success("Adjustment saved");
      form.reset();
      setDesignId(undefined);
      router.refresh();
    },
    onError: (err: ApiError) => {
      toast.error(err.detail ?? "Save failed");
    },
  });

  const onSubmit = (values: AdjustmentFormValues) => {
    mutation.mutate({
      stock_date: values.stock_date,
      entry_date: values.entry_date,
      design_id: values.design_id,
      entered_by_id: values.entered_by_id,
      lines: values.lines.map((l) => ({
        grade_id: l.grade_id,
        physical_cb: l.physical_cb,
      })),
    });
  };

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>New Stock Adjustment</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="stock_date">Stock date</Label>
            <Controller
              control={form.control}
              name="stock_date"
              render={({ field, fieldState }) => (
                <DatePicker
                  id="stock_date"
                  value={field.value}
                  onChange={(iso) => {
                    field.onChange(iso ?? "");
                    if (iso) setStockDate(iso);
                  }}
                  ariaInvalid={!!fieldState.error}
                  ariaDescribedBy={
                    fieldState.error ? "stock_date-error" : undefined
                  }
                />
              )}
            />
            {form.formState.errors.stock_date && (
              <p id="stock_date-error" role="alert" className="text-xs text-destructive">
                {form.formState.errors.stock_date.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="entry_date">Entry date</Label>
            <Controller
              control={form.control}
              name="entry_date"
              render={({ field, fieldState }) => (
                <DatePicker
                  id="entry_date"
                  value={field.value}
                  onChange={(iso) => field.onChange(iso ?? "")}
                  ariaInvalid={!!fieldState.error}
                  ariaDescribedBy={
                    fieldState.error ? "entry_date-error" : undefined
                  }
                />
              )}
            />
            {form.formState.errors.entry_date && (
              <p id="entry_date-error" role="alert" className="text-xs text-destructive">
                {form.formState.errors.entry_date.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="design_id">Design</Label>
            <Controller
              control={form.control}
              name="design_id"
              render={({ field }) => (
                <Select
                  value={field.value ? String(field.value) : ""}
                  onValueChange={(v) => {
                    const n = Number(v);
                    field.onChange(n);
                    setDesignId(n);
                  }}
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
              )}
            />
            {form.formState.errors.design_id && (
              <p role="alert" className="text-xs text-destructive">
                {form.formState.errors.design_id.message}
              </p>
            )}
          </div>

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
        </CardContent>
      </Card>

      {showErr012 && <Err012Banner designName={selectedDesign?.design_name} />}

      {!showErr012 && fields.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Grades</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {fields.map((field, index) => {
              const row = gradesWithCbQ.data?.[index];
              if (!row) return null;
              return (
                <Controller
                  key={field.id}
                  control={form.control}
                  name={`lines.${index}.physical_cb`}
                  render={({ field: pField, fieldState }) => (
                    <AdjustmentLineRow
                      index={index}
                      gradeCode={row.grade_code}
                      softwareCb={row.software_cb}
                      physicalCb={pField.value}
                      onChange={(v) => pField.onChange(v ?? 0)}
                      errorId={`adj-line-${index}-physical-error`}
                      errorMessage={fieldState.error?.message}
                    />
                  )}
                />
              );
            })}
          </CardContent>
        </Card>
      )}

      <div className="flex justify-end">
        <Button
          type="submit"
          disabled={mutation.isPending || showErr012}
          aria-busy={mutation.isPending}
        >
          {mutation.isPending ? "Saving..." : "Save Adjustment"}
        </Button>
      </div>
    </form>
  );
}
