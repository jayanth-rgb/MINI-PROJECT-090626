// TC-098..TC-102 — AdjustmentForm (F-009) tests
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AdjustmentForm } from "@/components/transactions/adjustment/AdjustmentForm";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: jest.fn(), push: jest.fn() }),
}));
jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn() },
}));

jest.mock("@/lib/api/masters", () => ({
  staffApi: {
    list: jest.fn().mockResolvedValue([
      { staff_id: 1, staff_name: "Chandran", is_active: true, created_at: "2026-06-23T00:00:00Z" },
    ]),
  },
  designsApi: {
    list: jest.fn().mockResolvedValue([
      { design_id: 1, size: "16X10", design_name: "16X10 Ridges", is_active: true, created_at: "2026-06-23T00:00:00Z" },
      { design_id: 3, size: "11X7", design_name: "Empty design", is_active: true, created_at: "2026-06-23T00:00:00Z" },
    ]),
  },
}));

const mockGetGradesWithCb = jest.fn();
const mockCreate = jest.fn();
jest.mock("@/lib/api/transactions", () => ({
  designsTxApi: {
    getGradesWithCb: (...args: unknown[]) => mockGetGradesWithCb(...args),
  },
  adjustmentsApi: {
    create: (...args: unknown[]) => mockCreate(...args),
  },
}));

function renderWithQuery() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <AdjustmentForm />
    </QueryClientProvider>
  );
}

beforeEach(() => {
  mockGetGradesWithCb.mockReset();
  mockCreate.mockReset();
});

describe("AdjustmentForm", () => {
  test("TC-098: stock_date > entry_date blocks submit (zod cross-field ERR-010)", async () => {
    const { adjustmentCreateSchema } = await import("@/lib/validation/transaction-schemas");
    const result = adjustmentCreateSchema.safeParse({
      stock_date: "2026-06-22",
      entry_date: "2026-06-21",
      design_id: 1,
      entered_by_id: 1,
      lines: [{ grade_id: 1, physical_cb: 10 }],
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(JSON.stringify(result.error.format())).toMatch(/on or before/i);
    }
  });

  test("TC-100: physical_cb = -1 rejected by zod refinement (ERR-009)", async () => {
    const { adjustmentLineCreateSchema } = await import("@/lib/validation/transaction-schemas");
    const result = adjustmentLineCreateSchema.safeParse({
      grade_id: 1,
      physical_cb: -1,
    });
    expect(result.success).toBe(false);
  });

  test("TC-099: getGradesWithCb populates AdjustmentLineRow per response with software_cb pre-filled", async () => {
    mockGetGradesWithCb.mockResolvedValue([
      { grade_id: 1, grade_code: "1", software_cb: 42 },
      { grade_id: 2, grade_code: "OB", software_cb: 17 },
    ]);
    const user = userEvent.setup();
    renderWithQuery();
    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: /^design$/i })).toBeEnabled()
    );
    await user.click(screen.getByRole("combobox", { name: /^design$/i }));
    await user.click(await screen.findByRole("option", { name: /16X10 Ridges/i }));
    await waitFor(() => {
      expect(screen.getByText(/Grade 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Grade OB/i)).toBeInTheDocument();
      expect(screen.getByText("42")).toBeInTheDocument();
      expect(screen.getByText("17")).toBeInTheDocument();
    });
  });

  test("TC-101: live-computed difference updates on physical_cb input", async () => {
    mockGetGradesWithCb.mockResolvedValue([
      { grade_id: 1, grade_code: "1", software_cb: 50 },
    ]);
    const user = userEvent.setup();
    renderWithQuery();
    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: /^design$/i })).toBeEnabled()
    );
    await user.click(screen.getByRole("combobox", { name: /^design$/i }));
    await user.click(await screen.findByRole("option", { name: /16X10 Ridges/i }));
    await waitFor(() => expect(screen.getByText(/Grade 1/i)).toBeInTheDocument());
    const physicalInput = screen.getByLabelText(/Grade 1/i) as HTMLInputElement;
    await user.clear(physicalInput);
    await user.type(physicalInput, "48");
    const diff = screen.getByTestId("adj-line-0-difference");
    await waitFor(() => expect(diff.textContent).toBe("-2"));
  });

  test("TC-102: empty getGradesWithCb response shows Err012Banner and disables submit", async () => {
    mockGetGradesWithCb.mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithQuery();
    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: /^design$/i })).toBeEnabled()
    );
    await user.click(screen.getByRole("combobox", { name: /^design$/i }));
    await user.click(await screen.findByRole("option", { name: /Empty design/i }));
    await waitFor(() =>
      expect(screen.getByTestId("err-012-banner")).toBeInTheDocument()
    );
    const submit = screen.getByRole("button", { name: /Save Adjustment/i });
    expect(submit).toBeDisabled();
  });
});
