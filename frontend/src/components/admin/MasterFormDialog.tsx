// T-034 — Reusable dialog wrapper for create + edit flows.
"use client";

import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
  formId: string;
  isSubmitting: boolean;
}

export function MasterFormDialog({
  open,
  onOpenChange,
  title,
  description,
  children,
  formId,
  isSubmitting,
}: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-[480px]"
        data-testid="master-form-dialog"
      >
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription className="sr-only">
            {description ?? title}
          </DialogDescription>
        </DialogHeader>
        <div className="py-2">{children}</div>
        <DialogFooter className="gap-2 sm:gap-3">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
            data-testid="dialog-cancel-btn"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            form={formId}
            disabled={isSubmitting}
            data-testid="dialog-save-btn"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              "Save"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
