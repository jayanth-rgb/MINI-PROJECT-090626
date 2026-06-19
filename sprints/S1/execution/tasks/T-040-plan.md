# T-040 — Design-Grade Map Admin (page + form)

**Module:** M-006 · **Depends on:** T-028, T-030, T-033, T-034 · **TC refs:** TC-045, TC-046 · **AC:** AC-016, AC-017

## Implementation logic

```tsx
// frontend/src/app/admin/design-grade-map/page.tsx
"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { designGradeMapApi, designsApi, gradesApi } from "@/lib/api/masters";
import type { DesignGradeMap, DesignGradeMapCreate } from "@/types/masters";
import { MasterDataTable } from "@/components/admin/MasterDataTable";
import { MasterFormDialog } from "@/components/admin/MasterFormDialog";
import { DesignGradeMapForm } from "@/components/admin/design-grade-map/DesignGradeMapForm";
import { Button } from "@/components/ui/button";

const QK_MAP = ["design-grade-map"] as const;
const QK_DESIGNS = ["designs"] as const;
const QK_GRADES = ["grades"] as const;

export default function DesignGradeMapPage() {
  const qc = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<DesignGradeMap | null>(null);

  const { data: rows = [] } = useQuery({ queryKey: QK_MAP, queryFn: () => designGradeMapApi.list(true) });
  const { data: designs = [] } = useQuery({ queryKey: QK_DESIGNS, queryFn: () => designsApi.list(false) });
  const { data: grades = [] } = useQuery({ queryKey: QK_GRADES, queryFn: () => gradesApi.list(false) });

  const createMut = useMutation({
    mutationFn: designGradeMapApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: QK_MAP }); setDialogOpen(false); },
    onError: (e: { message?: string }) => toast.error(e?.message ?? "Create failed", { className: "destructive" }),
  });

  const removeMut = useMutation({
    mutationFn: designGradeMapApi.remove,
    onSuccess: () => qc.invalidateQueries({ queryKey: QK_MAP }),
    onError: (e: { message?: string }) => toast.error(e?.message ?? "Deactivate failed"),
  });

  const FORM_ID = "design-grade-map-form";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Design-Grade Map</h2>
        <Button onClick={() => { setEditing(null); setDialogOpen(true); }}>New Mapping</Button>
      </div>

      <MasterDataTable<DesignGradeMap>
        rows={rows}
        columns={[
          { key: "map_id", label: "ID" },
          { key: "design_name", label: "Design" },
          { key: "grade_code", label: "Grade" },
        ]}
        rowKey={(r) => r.map_id}
        isActive={(r) => r.is_active}
        onEdit={(r) => { setEditing(r); setDialogOpen(true); }}
        onToggleActive={(r) => removeMut.mutate(r.map_id)}
      />

      <MasterFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Edit Mapping" : "New Mapping"}
        onSubmit={() => (document.getElementById(FORM_ID) as HTMLFormElement)?.requestSubmit()}
        isSubmitting={createMut.isPending}
      >
        <DesignGradeMapForm
          formId={FORM_ID}
          defaultValues={editing ?? { design_id: 0, grade_id: 0 }}
          designs={designs}
          grades={grades}
          onSubmit={(values) => createMut.mutate(values)}
        />
      </MasterFormDialog>
    </div>
  );
}
```

```tsx
// frontend/src/components/admin/design-grade-map/DesignGradeMapForm.tsx
"use client";

import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { designGradeMapSchema } from "@/lib/validation/master-schemas";
import type { DesignGradeMapCreate, Design, Grade } from "@/types/masters";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

interface Props {
  defaultValues: Partial<DesignGradeMapCreate>;
  designs: Design[];
  grades: Grade[];
  onSubmit: (values: DesignGradeMapCreate) => void;
  formId: string;
}

export function DesignGradeMapForm({
  defaultValues, designs, grades, onSubmit, formId,
}: Props) {
  const {
    control, handleSubmit, formState: { errors },
  } = useForm<DesignGradeMapCreate>({
    resolver: zodResolver(designGradeMapSchema),
    defaultValues: { design_id: 0, grade_id: 0, ...defaultValues },
  });

  return (
    <form id={formId} onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <div>
        <Label>Design</Label>
        <Controller
          name="design_id"
          control={control}
          render={({ field }) => (
            <Select value={String(field.value || "")} onValueChange={(v) => field.onChange(Number(v))}>
              <SelectTrigger><SelectValue placeholder="Select design" /></SelectTrigger>
              <SelectContent>
                {designs.filter((d) => d.is_active).map((d) => (
                  <SelectItem key={d.design_id} value={String(d.design_id)}>
                    {d.design_name} ({d.size})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
        {errors.design_id && <p className="text-sm text-destructive">{errors.design_id.message}</p>}
      </div>
      <div>
        <Label>Grade</Label>
        <Controller
          name="grade_id"
          control={control}
          render={({ field }) => (
            <Select value={String(field.value || "")} onValueChange={(v) => field.onChange(Number(v))}>
              <SelectTrigger><SelectValue placeholder="Select grade" /></SelectTrigger>
              <SelectContent>
                {grades.filter((g) => g.is_active).map((g) => (
                  <SelectItem key={g.grade_id} value={String(g.grade_id)}>
                    {g.grade_code}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
        {errors.grade_id && <p className="text-sm text-destructive">{errors.grade_id.message}</p>}
      </div>
    </form>
  );
}
```

## Constraints
- DS-011: form uses zodResolver; selects wired via Controller (shadcn Select is uncontrolled by default)
- Only is_active=true designs/grades appear in dropdowns
- AC-016 client surfacing: 409 -> destructive toast

## Do not touch
Any other file.

## Success criteria
- **Manual:** Create duplicate pair -> red toast; submit with neither selected -> two inline required errors
- **Automated:** TC-045 (toast on 409), TC-046 (form blocks empty selects)
- **DoD:** Page + Select-form rendered; dropdowns filter to active only

## Checkout prompt
*"Design-Grade Map admin — page + Select-based form; 409 toast (AC-016 client)."*
