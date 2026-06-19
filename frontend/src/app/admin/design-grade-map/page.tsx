// T-040 — Design-Grade Map admin page (F-006: AC-016 + AC-017).
// AC-016: 409 from duplicate (design_id, grade_id) surfaces as destructive toast.
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
import { DesignGradeMapForm } from "@/components/admin/design-grade-map/DesignGradeMapForm";
import { designGradeMapApi, designsApi, gradesApi } from "@/lib/api/masters";
import type { ApiError, DesignGradeMap } from "@/types/masters";
import type { DesignGradeMapFormValues } from "@/lib/validation/master-schemas";

const QK_MAP = ["design-grade-map"] as const;
const QK_DESIGNS = ["designs"] as const;
const QK_GRADES = ["grades"] as const;
const FORM_ID = "design-grade-map-form";

export default function DesignGradeMapPage() {
  const qc = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<DesignGradeMap | null>(null);

  const { data: rows = [], isLoading } = useQuery({
    queryKey: QK_MAP,
    queryFn: () => designGradeMapApi.list(true),
  });
  const { data: designs = [] } = useQuery({
    queryKey: QK_DESIGNS,
    queryFn: () => designsApi.list(false),
  });
  const { data: grades = [] } = useQuery({
    queryKey: QK_GRADES,
    queryFn: () => gradesApi.list(false),
  });

  const createMut = useMutation({
    mutationFn: designGradeMapApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK_MAP });
      toast.success("Mapping created successfully");
      setDialogOpen(false);
    },
    onError: (e: ApiError) =>
      toast.error(e.detail ?? "Could not create mapping"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<DesignGradeMap> }) =>
      designGradeMapApi.update(id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK_MAP });
      toast.success("Mapping updated successfully");
      setDialogOpen(false);
      setEditing(null);
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Update failed"),
  });

  const removeMut = useMutation({
    mutationFn: designGradeMapApi.remove,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK_MAP });
      toast.success("Mapping deactivated");
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Deactivate failed"),
  });

  const reactivateMut = useMutation({
    mutationFn: (id: number) => designGradeMapApi.update(id, { is_active: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK_MAP });
      toast.success("Mapping reactivated");
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Reactivate failed"),
  });

  const handleSubmit = (values: DesignGradeMapFormValues) => {
    if (editing) {
      updateMut.mutate({ id: editing.map_id, patch: values });
    } else {
      createMut.mutate(values);
    }
  };

  const columns: MasterDataTableColumn<DesignGradeMap>[] = [
    { key: "map_id", label: "ID" },
    { key: "design_name", label: "Design" },
    { key: "grade_code", label: "Grade" },
    {
      key: "is_active",
      label: "Status",
      render: (row) => statusBadge(row.is_active),
    },
  ];

  const submitting = createMut.isPending || updateMut.isPending;

  return (
    <div className="space-y-6" data-testid="design-grade-map-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Design-Grade Map</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Combinations available in transaction forms.
          </p>
        </div>
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
          data-testid="add-mapping-btn"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Mapping
        </Button>
      </div>

      <MasterDataTable<DesignGradeMap>
        rows={rows}
        columns={columns}
        rowKey={(r) => r.map_id}
        isActive={(r) => r.is_active}
        onEdit={(r) => {
          setEditing(r);
          setDialogOpen(true);
        }}
        onToggleActive={(r) =>
          r.is_active
            ? removeMut.mutate(r.map_id)
            : reactivateMut.mutate(r.map_id)
        }
        isLoading={isLoading}
      />

      <MasterFormDialog
        open={dialogOpen}
        onOpenChange={(o) => {
          setDialogOpen(o);
          if (!o) setEditing(null);
        }}
        title={editing ? "Edit Mapping" : "Add Mapping"}
        formId={FORM_ID}
        isSubmitting={submitting}
      >
        <DesignGradeMapForm
          key={editing?.map_id ?? "new"}
          formId={FORM_ID}
          defaultValues={
            editing
              ? { design_id: editing.design_id, grade_id: editing.grade_id }
              : { design_id: 0, grade_id: 0 }
          }
          designs={designs}
          grades={grades}
          onSubmit={handleSubmit}
        />
      </MasterFormDialog>
    </div>
  );
}
