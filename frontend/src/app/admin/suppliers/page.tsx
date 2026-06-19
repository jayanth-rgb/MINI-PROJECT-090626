// T-035 — Suppliers admin page (F-001: AC-001 + AC-002).
"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  MasterDataTable,
  statusBadge,
  type MasterDataTableColumn,
} from "@/components/admin/MasterDataTable";
import { MasterFormDialog } from "@/components/admin/MasterFormDialog";
import { SupplierForm } from "@/components/admin/suppliers/SupplierForm";
import { suppliersApi } from "@/lib/api/masters";
import type { ApiError, Supplier } from "@/types/masters";
import type { SupplierFormValues } from "@/lib/validation/master-schemas";

const QK = ["suppliers"] as const;
const FORM_ID = "supplier-form";

export default function SuppliersPage() {
  const qc = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Supplier | null>(null);

  const { data: rows = [], isLoading } = useQuery({
    queryKey: QK,
    queryFn: () => suppliersApi.list(true),
  });

  const createMut = useMutation({
    mutationFn: suppliersApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Supplier created successfully");
      setDialogOpen(false);
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Create failed"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<Supplier> }) =>
      suppliersApi.update(id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Supplier updated successfully");
      setDialogOpen(false);
      setEditing(null);
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Update failed"),
  });

  const removeMut = useMutation({
    mutationFn: suppliersApi.remove,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Supplier deactivated");
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Deactivate failed"),
  });

  const reactivateMut = useMutation({
    mutationFn: (id: number) => suppliersApi.update(id, { is_active: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Supplier reactivated");
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Reactivate failed"),
  });

  const handleSubmit = (values: SupplierFormValues) => {
    if (editing) {
      updateMut.mutate({ id: editing.supplier_id, patch: values });
    } else {
      createMut.mutate(values);
    }
  };

  const columns: MasterDataTableColumn<Supplier>[] = [
    { key: "supplier_id", label: "ID" },
    { key: "supplier_name", label: "Name" },
    { key: "place", label: "Place" },
    {
      key: "is_active",
      label: "Status",
      render: (row) => statusBadge(row.is_active),
    },
  ];

  const submitting = createMut.isPending || updateMut.isPending;

  return (
    <div className="space-y-6" data-testid="suppliers-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Suppliers</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage suppliers feeding the Inward Form.
          </p>
        </div>
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
          data-testid="add-supplier-btn"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Supplier
        </Button>
      </div>

      <MasterDataTable<Supplier>
        rows={rows}
        columns={columns}
        rowKey={(r) => r.supplier_id}
        isActive={(r) => r.is_active}
        onEdit={(r) => {
          setEditing(r);
          setDialogOpen(true);
        }}
        onToggleActive={(r) =>
          r.is_active
            ? removeMut.mutate(r.supplier_id)
            : reactivateMut.mutate(r.supplier_id)
        }
        isLoading={isLoading}
      />

      <MasterFormDialog
        open={dialogOpen}
        onOpenChange={(o) => {
          setDialogOpen(o);
          if (!o) setEditing(null);
        }}
        title={editing ? "Edit Supplier" : "Add Supplier"}
        formId={FORM_ID}
        isSubmitting={submitting}
      >
        <SupplierForm
          key={editing?.supplier_id ?? "new"}
          formId={FORM_ID}
          defaultValues={editing ?? { supplier_name: "", place: "" }}
          onSubmit={handleSubmit}
        />
      </MasterFormDialog>
    </div>
  );
}
