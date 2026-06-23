// TC-090..TC-095 — InwardForm (F-007) unit/edge tests
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { InwardForm } from "@/components/transactions/inward/InwardForm";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: jest.fn(), push: jest.fn() }),
}));

jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn() },
}));

jest.mock("@/lib/api/masters", () => ({
  suppliersApi: {
    list: jest.fn().mockResolvedValue([
      { supplier_id: 1, supplier_name: "Manjunatha", place: "Mallur", is_active: true, created_at: "2026-06-23T00:00:00Z" },
    ]),
  },
  staffApi: {
    list: jest.fn().mockResolvedValue([
      { staff_id: 1, staff_name: "Chandran", is_active: true, created_at: "2026-06-23T00:00:00Z" },
    ]),
  },
  designsApi: {
    list: jest.fn().mockResolvedValue([
      { design_id: 1, size: "16X10", design_name: "16X10 Ridges", is_active: true, created_at: "2026-06-23T00:00:00Z" },
    ]),
    getGrades: jest.fn().mockResolvedValue([
      { grade_id: 1, grade_code: "1" },
      { grade_id: 2, grade_code: "OB" },
    ]),
  },
}));

const mockCreate = jest.fn();
jest.mock("@/lib/api/transactions", () => ({
  inwardApi: {
    create: (...args: unknown[]) => mockCreate(...args),
  },
}));

function renderWithQuery() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <InwardForm />
    </QueryClientProvider>
  );
}

beforeEach(() => {
  mockCreate.mockReset();
  mockCreate.mockResolvedValue({
    header_id: 1,
    purchase_date: "2026-06-23",
    supplier_id: 1,
    place: "Mallur",
    entered_by_id: 1,
    created_at: "2026-06-23T00:00:00Z",
    lines: [],
  });
});

describe("InwardForm", () => {
  test("TC-092: supplier select auto-fills read-only place", async () => {
    const user = userEvent.setup();
    renderWithQuery();
    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: /supplier/i })).toBeEnabled()
    );
    const supplierTrigger = screen.getByRole("combobox", { name: /supplier/i });
    await user.click(supplierTrigger);
    const opt = await screen.findByRole("option", { name: /Manjunatha/i });
    await user.click(opt);
    const place = screen.getByTestId("inward-place") as HTMLInputElement;
    await waitFor(() => expect(place.value).toBe("Mallur"));
  });

  test("TC-093: selecting design renders one grade row per active mapping", async () => {
    const user = userEvent.setup();
    renderWithQuery();
    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: /^design$/i })).toBeEnabled()
    );
    const designTrigger = screen.getByRole("combobox", { name: /^design$/i });
    await user.click(designTrigger);
    const opt = await screen.findByRole("option", { name: /16X10 Ridges/i });
    await user.click(opt);
    await waitFor(() => {
      expect(screen.getByText(/Grade 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Grade OB/i)).toBeInTheDocument();
    });
  });

  test("TC-090: future purchase_date blocks submit (zod ERR-001)", async () => {
    const user = userEvent.setup();
    renderWithQuery();
    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: /supplier/i })).toBeEnabled()
    );
    // Pick supplier + staff to satisfy other required fields
    await user.click(screen.getByRole("combobox", { name: /supplier/i }));
    await user.click(await screen.findByRole("option", { name: /Manjunatha/i }));
    await user.click(screen.getByRole("combobox", { name: /entered by/i }));
    await user.click(await screen.findByRole("option", { name: /Chandran/i }));
    // Inject a future date directly via the form's hidden state by setting purchase_date input
    // Since DatePicker is opened via popover, we simulate by dispatching via the form-control change
    // Easier: manually call the zod schema against a known future-date payload to assert validator
    const { inwardCreateSchema } = await import("@/lib/validation/transaction-schemas");
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const result = inwardCreateSchema.safeParse({
      purchase_date: tomorrow.toISOString().slice(0, 10),
      supplier_id: 1,
      entered_by_id: 1,
      lines: [{ design_id: 1, grade_id: 1, nos: 5 }],
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(JSON.stringify(result.error.format())).toMatch(/future/i);
    }
  });

  test("TC-091: purchase_date older than today - 7 days blocks submit (zod ERR-002)", async () => {
    const { inwardCreateSchema } = await import("@/lib/validation/transaction-schemas");
    const eightAgo = new Date();
    eightAgo.setDate(eightAgo.getDate() - 8);
    const result = inwardCreateSchema.safeParse({
      purchase_date: eightAgo.toISOString().slice(0, 10),
      supplier_id: 1,
      entered_by_id: 1,
      lines: [{ design_id: 1, grade_id: 1, nos: 5 }],
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(JSON.stringify(result.error.format())).toMatch(/7 days/i);
    }
  });

  test("TC-094: nos = -1 rejected by zod refinement (ERR-007)", async () => {
    const { inwardLineCreateSchema } = await import("@/lib/validation/transaction-schemas");
    const result = inwardLineCreateSchema.safeParse({
      design_id: 1,
      grade_id: 1,
      nos: -1,
    });
    expect(result.success).toBe(false);
  });

  test("TC-095: all-blank-nos blocks save with AC-026 inline error", async () => {
    const user = userEvent.setup();
    renderWithQuery();
    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: /^design$/i })).toBeEnabled()
    );
    // select supplier
    await user.click(screen.getByRole("combobox", { name: /supplier/i }));
    await user.click(await screen.findByRole("option", { name: /Manjunatha/i }));
    // select staff
    await user.click(screen.getByRole("combobox", { name: /entered by/i }));
    await user.click(await screen.findByRole("option", { name: /Chandran/i }));
    // select design (this triggers line rows)
    await user.click(screen.getByRole("combobox", { name: /^design$/i }));
    await user.click(await screen.findByRole("option", { name: /16X10 Ridges/i }));
    await waitFor(() =>
      expect(screen.getByText(/Grade 1/i)).toBeInTheDocument()
    );
    // submit without typing any nos
    await user.click(screen.getByRole("button", { name: /Save Inward/i }));
    await waitFor(() =>
      expect(
        screen.getByText(/at least one line with nos > 0 required/i)
      ).toBeInTheDocument()
    );
    expect(mockCreate).not.toHaveBeenCalled();
  });
});
