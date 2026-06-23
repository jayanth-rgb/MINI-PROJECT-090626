import { InwardForm } from "@/components/transactions/inward/InwardForm";

export const metadata = { title: "New Inward — Jayanth Trading" };

export default function NewInwardPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">New Inward</h1>
        <p className="text-sm text-muted-foreground">
          Record a new inward purchase. Place auto-fills from supplier.
        </p>
      </header>
      <InwardForm />
    </div>
  );
}
