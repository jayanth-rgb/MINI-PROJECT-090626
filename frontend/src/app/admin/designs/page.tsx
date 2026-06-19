// T-039 — Designs admin page (F-005: AC-013 + AC-015).
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
import { DesignForm } from "@/components/admin/designs/DesignForm";
import { designsApi } from "@/lib/api/masters";
import type { ApiError, Design } from "@/types/masters";
import type { DesignFormValues } from "@/lib/validation/master-schemas";

const QK = ["designs"] as const;
const FORM_ID = "design-form";

export default function DesignsPage() {
  const qc = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Design | null>(null);

  const { data: rows = [], isLoading } = useQuery({
    queryKey: QK,
    queryFn: () => designsApi.list(true),
  });

  const createMut = useMutation({
    mutationFn: designsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Design created successfully");
      setDialogOpen(false);
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Create failed"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<Design> }) =>
      designsApi.update(id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Design updated successfully");
      setDialogOpen(false);
      setEditing(null);
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Update failed"),
  });

  const removeMut = useMutation({
    mutationFn: designsApi.remove,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Design deactivated");
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Deactivate failed"),
  });

  const reactivateMut = useMutation({
    mutationFn: (id: number) => designsApi.update(id, { is_active: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Design reactivated");
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Reactivate failed"),
  });

  const handleSubmit = (values: DesignFormValues) => {
    if (editing) {
      updateMut.mutate({ id: editing.design_id, patch: values });
    } else {
      createMut.mutate(values);
    }
  };

  const columns: MasterDataTableColumn<Design>[] = [
    { key: "design_id", label: "ID" },
    { key: "size", label: "Size" },
    { key: "design_name", label: "Design Name" },
    {
      key: "is_active",
      label: "Status",
      render: (row) => statusBadge(row.is_active),
    },
  ];

  const submitting = createMut.isPending || updateMut.isPending;

  return (
    <div className="space-y-6" data-testid="designs-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Trading Designs</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Tile sizes and their design names.
          </p>
        </div>
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
          data-testid="add-design-btn"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Design
        </Button>
      </div>

      <MasterDataTable<Design>
        rows={rows}
        columns={columns}
        rowKey={(r) => r.design_id}
        isActive={(r) => r.is_active}
        onEdit={(r) => {
          setEditing(r);
          setDialogOpen(true);
        }}
        onToggleActive={(r) =>
          r.is_active
            ? removeMut.mutate(r.design_id)
            : reactivateMut.mutate(r.design_id)
        }
        isLoading={isLoading}
      />

      <MasterFormDialog
        open={dialogOpen}
        onOpenChange={(o) => {
          setDialogOpen(o);
          if (!o) setEditing(null);
        }}
        title={editing ? "Edit Design" : "Add Design"}
        formId={FORM_ID}
        isSubmitting={submitting}
      >
        <DesignForm
          key={editing?.design_id ?? "new"}
          formId={FORM_ID}
          defaultValues={editing ?? { size: "", design_name: "" }}
          onSubmit={handleSubmit}
        />
      </MasterFormDialog>
    </div>
  );
}
