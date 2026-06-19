// T-038 — Grades admin page (F-004: AC-011 UNIQUE, AC-012 deactivate).
// 409 from backend (or scaffold mock) surfaces as destructive toast.
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
import { GradeForm } from "@/components/admin/grades/GradeForm";
import { gradesApi } from "@/lib/api/masters";
import type { ApiError, Grade } from "@/types/masters";
import type { GradeFormValues } from "@/lib/validation/master-schemas";

const QK = ["grades"] as const;
const FORM_ID = "grade-form";

export default function GradesPage() {
  const qc = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Grade | null>(null);

  const { data: rows = [], isLoading } = useQuery({
    queryKey: QK,
    queryFn: () => gradesApi.list(true),
  });

  const createMut = useMutation({
    mutationFn: gradesApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Grade created successfully");
      setDialogOpen(false);
    },
    // AC-011: 409 toast keeps dialog open so user can fix the duplicate.
    onError: (e: ApiError) =>
      toast.error(e.detail ?? "Could not create grade"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<Grade> }) =>
      gradesApi.update(id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Grade updated successfully");
      setDialogOpen(false);
      setEditing(null);
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Update failed"),
  });

  const removeMut = useMutation({
    mutationFn: gradesApi.remove,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Grade deactivated");
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Deactivate failed"),
  });

  const reactivateMut = useMutation({
    mutationFn: (id: number) => gradesApi.update(id, { is_active: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK });
      toast.success("Grade reactivated");
    },
    onError: (e: ApiError) => toast.error(e.detail ?? "Reactivate failed"),
  });

  const handleSubmit = (values: GradeFormValues) => {
    if (editing) {
      updateMut.mutate({ id: editing.grade_id, patch: values });
    } else {
      createMut.mutate(values);
    }
  };

  const columns: MasterDataTableColumn<Grade>[] = [
    { key: "grade_id", label: "ID" },
    { key: "grade_code", label: "Grade Code" },
    {
      key: "is_active",
      label: "Status",
      render: (row) => statusBadge(row.is_active),
    },
  ];

  const submitting = createMut.isPending || updateMut.isPending;

  return (
    <div className="space-y-6" data-testid="grades-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Grades</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Tile-quality grades — codes are unique.
          </p>
        </div>
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
          data-testid="add-grade-btn"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Grade
        </Button>
      </div>

      <MasterDataTable<Grade>
        rows={rows}
        columns={columns}
        rowKey={(r) => r.grade_id}
        isActive={(r) => r.is_active}
        onEdit={(r) => {
          setEditing(r);
          setDialogOpen(true);
        }}
        onToggleActive={(r) =>
          r.is_active
            ? removeMut.mutate(r.grade_id)
            : reactivateMut.mutate(r.grade_id)
        }
        isLoading={isLoading}
      />

      <MasterFormDialog
        open={dialogOpen}
        onOpenChange={(o) => {
          setDialogOpen(o);
          if (!o) setEditing(null);
        }}
        title={editing ? "Edit Grade" : "Add Grade"}
        formId={FORM_ID}
        isSubmitting={submitting}
      >
        <GradeForm
          key={editing?.grade_id ?? "new"}
          formId={FORM_ID}
          defaultValues={editing ?? { grade_code: "" }}
          onSubmit={handleSubmit}
        />
      </MasterFormDialog>
    </div>
  );
}
