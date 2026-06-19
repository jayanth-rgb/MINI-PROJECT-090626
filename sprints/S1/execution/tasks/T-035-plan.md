# T-035 — Suppliers Admin (page + form)

**Module:** M-006 · **Depends on:** T-028, T-030, T-033, T-034 · **TC refs:** TC-039, TC-040 · **AC:** AC-001, AC-002

## Implementation logic

```tsx
// frontend/src/app/admin/suppliers/page.tsx
"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { suppliersApi } from "@/lib/api/masters";
import type { Supplier, SupplierCreate } from "@/types/masters";
import { MasterDataTable } from "@/components/admin/MasterDataTable";
import { MasterFormDialog } from "@/components/admin/MasterFormDialog";
import { SupplierForm } from "@/components/admin/suppliers/SupplierForm";
import { Button } from "@/components/ui/button";

const QK = ["suppliers"] as const;

export default function SuppliersPage() {
  const qc = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Supplier | null>(null);

  const { data: suppliers = [] } = useQuery({
    queryKey: QK,
    queryFn: () => suppliersApi.list(true),
  });

  const createMut = useMutation({
    mutationFn: suppliersApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: QK }); setDialogOpen(false); },
    onError: (e: { message?: string }) => toast.error(e?.message ?? "Create failed"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<SupplierCreate> }) =>
      suppliersApi.update(id, patch),
    onSuccess: () => { qc.invalidateQueries({ queryKey: QK }); setDialogOpen(false); setEditing(null); },
    onError: (e: { message?: string }) => toast.error(e?.message ?? "Update failed"),
  });

  const removeMut = useMutation({
    mutationFn: suppliersApi.remove,
    onSuccess: () => qc.invalidateQueries({ queryKey: QK }),
    onError: (e: { message?: string }) => toast.error(e?.message ?? "Deactivate failed"),
  });

  const FORM_ID = "supplier-form";
  const submitting = createMut.isPending || updateMut.isPending;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Suppliers</h2>
        <Button onClick={() => { setEditing(null); setDialogOpen(true); }}>New Supplier</Button>
      </div>

      <MasterDataTable<Supplier>
        rows={suppliers}
        columns={[
          { key: "supplier_id", label: "ID" },
          { key: "supplier_name", label: "Name" },
          { key: "place", label: "Place" },
        ]}
        rowKey={(r) => r.supplier_id}
        isActive={(r) => r.is_active}
        onEdit={(r) => { setEditing(r); setDialogOpen(true); }}
        onToggleActive={(r) => removeMut.mutate(r.supplier_id)}
      />

      <MasterFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Edit Supplier" : "New Supplier"}
        onSubmit={() => (document.getElementById(FORM_ID) as HTMLFormElement)?.requestSubmit()}
        isSubmitting={submitting}
      >
        <SupplierForm
          formId={FORM_ID}
          defaultValues={editing ?? { supplier_name: "", place: "" }}
          onSubmit={(values) =>
            editing
              ? updateMut.mutate({ id: editing.supplier_id, patch: values })
              : createMut.mutate(values)
          }
        />
      </MasterFormDialog>
    </div>
  );
}
```

```tsx
// frontend/src/components/admin/suppliers/SupplierForm.tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { supplierSchema } from "@/lib/validation/master-schemas";
import type { SupplierCreate } from "@/types/masters";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Props {
  defaultValues: Partial<SupplierCreate>;
  onSubmit: (values: SupplierCreate) => void;
  formId: string;
}

export function SupplierForm({ defaultValues, onSubmit, formId }: Props) {
  const {
    register, handleSubmit, formState: { errors },
  } = useForm<SupplierCreate>({
    resolver: zodResolver(supplierSchema),
    defaultValues: { supplier_name: "", place: "", ...defaultValues },
  });

  return (
    <form id={formId} onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <div>
        <Label htmlFor="supplier_name">Name</Label>
        <Input id="supplier_name" {...register("supplier_name")} />
        {errors.supplier_name && <p className="text-sm text-destructive">{errors.supplier_name.message}</p>}
      </div>
      <div>
        <Label htmlFor="place">Place</Label>
        <Input id="place" {...register("place")} />
        {errors.place && <p className="text-sm text-destructive">{errors.place.message}</p>}
      </div>
    </form>
  );
}
```

## Constraints
- DS-011: hand-rolled Label+Input pairs (no shadcn form.tsx shim)
- Page reads `is_active` to render muted; deactivate flows through `removeMut`
- Form uses formId so MasterFormDialog Save button can trigger requestSubmit()

## Do not touch
Any other file.

## Success criteria
- **Manual:** /admin/suppliers loads; create/edit/deactivate roundtrip works against running backend
- **Automated:** TC-039 (empty supplier_name blocks), TC-040 (Deactivate calls remove + muted row)
- **DoD:** Page + form rendered; queries invalidated on success

## Checkout prompt
*"Suppliers admin — page + form. AC-001 + AC-002 covered."*
