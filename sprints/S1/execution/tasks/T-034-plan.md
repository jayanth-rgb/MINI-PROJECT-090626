# T-034 — MasterFormDialog

**Module:** M-006 · **Depends on:** — · **TC refs:** — (indirect) · **AC:** —

## Implementation logic

```tsx
// frontend/src/components/admin/MasterFormDialog.tsx
"use client";

import type { ReactNode } from "react";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  children: ReactNode;
  onSubmit: () => void;
  isSubmitting: boolean;
}

export function MasterFormDialog({
  open, onOpenChange, title, children, onSubmit, isSubmitting,
}: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="py-2">{children}</div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

## Constraints
- onSubmit is a handle passed by parent (which calls react-hook-form handleSubmit)
- Disable both Save and Cancel while isSubmitting to avoid mid-flight close

## Do not touch
Any other file.

## Success criteria
- **Manual:** Open dialog -> children render; Save calls onSubmit
- **Automated:** Indirect via TC-040/043/045
- **DoD:** Save disabled while isSubmitting

## Checkout prompt
*"MasterFormDialog — Dialog wrapper with Save/Cancel footer."*
