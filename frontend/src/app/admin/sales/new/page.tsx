import { SalesForm } from "@/components/transactions/sales/SalesForm";

export const metadata = { title: "New Sale — Jayanth Trading" };

export default function NewSalePage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">New Sale</h1>
        <p className="text-sm text-muted-foreground">
          Record a new sale. Place auto-fills from dealer.
        </p>
      </header>
      <SalesForm />
    </div>
  );
}
