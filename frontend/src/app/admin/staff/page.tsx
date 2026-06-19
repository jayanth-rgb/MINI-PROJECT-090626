// T-036 — Staff admin page (F-002: AC-004 + AC-005).
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
import { StaffForm } from "@/components/admin/staff/StaffForm";
import { staffApi } from "@/lib/api/masters";
import type { ApiError, Staff } from "@/types/masters";
import type { StaffFormValues } from "@/lib/validation/master-schemas";

const QK = ["staff"] as const;
const FORM_ID = "staff-form";

export default function StaffPage() {
  const qc = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Staff | null>(null);

  const { data: rows = [], isLoading } = useQuery({
    queryKey: QK,
    queryFn: () => staffApi.list(true),
  });

  const createMut = useMutation({
    mutationFn: staffApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Staff created successfully");
      setDialogOpen(false);
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Create failed"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<Staff> }) =>
      staffApi.update(id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Staff updated successfully");
      setDialogOpen(false);
      setEditing(null);
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Update failed"),
  });

  const removeMut = useMutation({
    mutationFn: staffApi.remove,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Staff deactivated");
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Deactivate failed"),
  });

  const reactivateMut = useMutation({
    mutationFn: (id: number) => staffApi.update(id, { is_active: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Staff reactivated");
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Reactivate failed"),
  });

  const handleSubmit = (values: StaffFormValues) => {
    if (editing) {
      updateMut.mutate({ id: editing.staff_id, patch: values });
    } else {
      createMut.mutate(values);
    }
  };

  const columns: MasterDataTableColumn<Staff>[] = [
    { key: "staff_id", label: "ID" },
    { key: "staff_name", label: "Name" },
    {
      key: "is_active",
      label: "Status",
      render: (row) => statusBadge(row.is_active),
    },
  ];

  const submitting = createMut.isPending || updateMut.isPending;

  return (
    <div className="space-y-6" data-testid="staff-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Staff</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Loading + verification staff who appear in transaction forms.
          </p>
        </div>
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
          data-testid="add-staff-btn"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Staff
        </Button>
      </div>

      <MasterDataTable<Staff>
        rows={rows}
        columns={columns}
        rowKey={(r) => r.staff_id}
        isActive={(r) => r.is_active}
        onEdit={(r) => {
          setEditing(r);
          setDialogOpen(true);
        }}
        onToggleActive={(r) =>
          r.is_active
            ? removeMut.mutate(r.staff_id)
            : reactivateMut.mutate(r.staff_id)
        }
        isLoading={isLoading}
      />

      <MasterFormDialog
        open={dialogOpen}
        onOpenChange={(o) => {
          setDialogOpen(o);
          if (!o) setEditing(null);
        }}
        title={editing ? "Edit Staff" : "Add Staff"}
        formId={FORM_ID}
        isSubmitting={submitting}
      >
        <StaffForm
          key={editing?.staff_id ?? "new"}
          formId={FORM_ID}
          defaultValues={editing ?? { staff_name: "" }}
          onSubmit={handleSubmit}
        />
      </MasterFormDialog>
    </div>
  );
}
