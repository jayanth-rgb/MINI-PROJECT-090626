import { AdjustmentForm } from "@/components/transactions/adjustment/AdjustmentForm";

export const metadata = { title: "New Adjustment — Jayanth Trading" };

export default function NewAdjustmentPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">New Stock Adjustment</h1>
        <p className="text-sm text-muted-foreground">
          Reconcile software balance with physical count. Software CB auto-pulls
          from the ledger.
        </p>
      </header>
      <AdjustmentForm />
    </div>
  );
}
