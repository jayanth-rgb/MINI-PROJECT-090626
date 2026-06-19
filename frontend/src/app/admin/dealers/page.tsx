// T-037 — Dealers admin page (F-003: AC-007 + AC-008).
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
import { DealerForm } from "@/components/admin/dealers/DealerForm";
import { dealersApi } from "@/lib/api/masters";
import type { ApiError, Dealer } from "@/types/masters";
import type { DealerFormValues } from "@/lib/validation/master-schemas";

const QK = ["dealers"] as const;
const FORM_ID = "dealer-form";

export default function DealersPage() {
  const qc = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Dealer | null>(null);

  const { data: rows = [], isLoading } = useQuery({
    queryKey: QK,
    queryFn: () => dealersApi.list(true),
  });

  const createMut = useMutation({
    mutationFn: dealersApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Dealer created successfully");
      setDialogOpen(false);
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Create failed"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<Dealer> }) =>
      dealersApi.update(id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Dealer updated successfully");
      setDialogOpen(false);
      setEditing(null);
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Update failed"),
  });

  const removeMut = useMutation({
    mutationFn: dealersApi.remove,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Dealer deactivated");
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Deactivate failed"),
  });

  const reactivateMut = useMutation({
    mutationFn: (id: number) => dealersApi.update(id, { is_active: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Dealer reactivated");
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Reactivate failed"),
  });

  const handleSubmit = (values: DealerFormValues) => {
    if (editing) {
      updateMut.mutate({ id: editing.dealer_id, patch: values });
    } else {
      createMut.mutate(values);
    }
  };

  const columns: MasterDataTableColumn<Dealer>[] = [
    { key: "dealer_id", label: "ID" },
    { key: "dealer_name", label: "Name" },
    { key: "place", label: "Place" },
    {
      key: "is_active",
      label: "Status",
      render: (row) => statusBadge(row.is_active),
    },
  ];

  const submitting = createMut.isPending || updateMut.isPending;

  return (
    <div className="space-y-6" data-testid="dealers-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dealers</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage dealers feeding the Sales Form + Sales Report.
          </p>
        </div>
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
          data-testid="add-dealer-btn"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Dealer
        </Button>
      </div>

      <MasterDataTable<Dealer>
        rows={rows}
        columns={columns}
        rowKey={(r) => r.dealer_id}
        isActive={(r) => r.is_active}
        onEdit={(r) => {
          setEditing(r);
          setDialogOpen(true);
        }}
        onToggleActive={(r) =>
          r.is_active
            ? removeMut.mutate(r.dealer_id)
            : reactivateMut.mutate(r.dealer_id)
        }
        isLoading={isLoading}
      />

      <MasterFormDialog
        open={dialogOpen}
        onOpenChange={(o) => {
          setDialogOpen(o);
          if (!o) setEditing(null);
        }}
        title={editing ? "Edit Dealer" : "Add Dealer"}
        formId={FORM_ID}
        isSubmitting={submitting}
      >
        <DealerForm
          key={editing?.dealer_id ?? "new"}
          formId={FORM_ID}
          defaultValues={editing ?? { dealer_name: "", place: "" }}
          onSubmit={handleSubmit}
        />
      </MasterFormDialog>
    </div>
  );
}
