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

import { dealersApi, staffApi, designsApi } from "@/lib/api/masters";
import { salesApi } from "@/lib/api/transactions";
import {
  salesCreateSchema,
  type SalesFormValues,
} from "@/lib/validation/transaction-schemas";
import type { SalesCreate } from "@/types/transactions";
import type { ApiError } from "@/types/masters";

export function SalesForm() {
  const router = useRouter();
  const [designId, setDesignId] = useState<number | undefined>(undefined);

  const dealersQ = useQuery({
    queryKey: ["dealers"],
    queryFn: () => dealersApi.list(),
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

  const form = useForm<SalesFormValues>({
    resolver: zodResolver(salesCreateSchema),
    defaultValues: {
      sales_date: new Date().toISOString().slice(0, 10),
      dealer_id: 0,
      loading_staff_id: 0,
      verified_by_id: 0,
      lines: [],
    },
    mode: "onSubmit",
  });
  const { fields, replace } = useFieldArray({
    control: form.control,
    name: "lines",
  });

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

  const dealerId = form.watch("dealer_id");
  const selectedDealer = dealersQ.data?.find(
    (d) => d.dealer_id === Number(dealerId)
  );

  const mutation = useMutation({
    mutationFn: (payload: SalesCreate) => salesApi.create(payload),
    onSuccess: () => {
      toast.success("Sale saved");
      form.reset();
      setDesignId(undefined);
      router.refresh();
    },
    onError: (err: ApiError) => {
      toast.error(err.detail ?? "Save failed");
    },
  });

  const onSubmit = (values: SalesFormValues) => {
    const lines = values.lines
      .filter((l) => l.nos != null && l.nos > 0)
      .map((l) => ({
        design_id: l.design_id,
        grade_id: l.grade_id,
        nos: l.nos as number,
      }));
    mutation.mutate({
      sales_date: values.sales_date,
      dealer_id: values.dealer_id,
      loading_staff_id: values.loading_staff_id,
      verified_by_id: values.verified_by_id,
      lines,
    });
  };

  const linesError = form.formState.errors.lines?.message as string | undefined;

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>New Sale</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="sales_date">Sales date</Label>
            <Controller
              control={form.control}
              name="sales_date"
              render={({ field, fieldState }) => (
                <DatePicker
                  id="sales_date"
                  value={field.value}
                  onChange={(iso) => field.onChange(iso ?? "")}
                  ariaInvalid={!!fieldState.error}
                  ariaDescribedBy={
                    fieldState.error ? "sales_date-error" : undefined
                  }
                />
              )}
            />
            {form.formState.errors.sales_date && (
              <p id="sales_date-error" role="alert" className="text-xs text-destructive">
                {form.formState.errors.sales_date.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="dealer_id">Dealer</Label>
            <Controller
              control={form.control}
              name="dealer_id"
              render={({ field }) => (
                <Select
                  value={field.value ? String(field.value) : ""}
                  onValueChange={(v) => field.onChange(Number(v))}
                >
                  <SelectTrigger id="dealer_id" aria-required="true">
                    <SelectValue placeholder="Select dealer" />
                  </SelectTrigger>
                  <SelectContent>
                    {dealersQ.data?.map((d) => (
                      <SelectItem key={d.dealer_id} value={String(d.dealer_id)}>
                        {d.dealer_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {form.formState.errors.dealer_id && (
              <p role="alert" className="text-xs text-destructive">
                {form.formState.errors.dealer_id.message}
              </p>
            )}
          </div>

          {/* Place — read-only mirror of dealer.place per DS-013 / AC-029 */}
          <div className="space-y-1.5">
            <Label htmlFor="place">Place</Label>
            <Input
              id="place"
              data-testid="sales-place"
              value={selectedDealer?.place ?? ""}
              readOnly
              placeholder="Auto-filled from dealer"
              className="bg-muted"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="loading_staff_id">Loading staff</Label>
            <Controller
              control={form.control}
              name="loading_staff_id"
              render={({ field }) => (
                <Select
                  value={field.value ? String(field.value) : ""}
                  onValueChange={(v) => field.onChange(Number(v))}
                >
                  <SelectTrigger id="loading_staff_id" aria-required="true">
                    <SelectValue placeholder="Select loading staff" />
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
            {form.formState.errors.loading_staff_id && (
              <p role="alert" className="text-xs text-destructive">
                {form.formState.errors.loading_staff_id.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="verified_by_id">Verified by</Label>
            <Controller
              control={form.control}
              name="verified_by_id"
              render={({ field }) => (
                <Select
                  value={field.value ? String(field.value) : ""}
                  onValueChange={(v) => field.onChange(Number(v))}
                >
                  <SelectTrigger id="verified_by_id" aria-required="true">
                    <SelectValue placeholder="Select verifier" />
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
            {form.formState.errors.verified_by_id && (
              <p role="alert" className="text-xs text-destructive">
                {form.formState.errors.verified_by_id.message}
              </p>
            )}
          </div>

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
          {mutation.isPending ? "Saving..." : "Save Sale"}
        </Button>
      </div>
    </form>
  );
}
