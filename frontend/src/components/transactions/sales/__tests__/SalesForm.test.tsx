// TC-096, TC-097 — SalesForm (F-008) edge tests
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { SalesForm } from "@/components/transactions/sales/SalesForm";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: jest.fn(), push: jest.fn() }),
}));
jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn() },
}));

jest.mock("@/lib/api/masters", () => ({
  dealersApi: {
    list: jest.fn().mockResolvedValue([
      { dealer_id: 1, dealer_name: "Raj Hardwares", place: "Dindivanam", is_active: true, created_at: "2026-06-23T00:00:00Z" },
    ]),
  },
  staffApi: {
    list: jest.fn().mockResolvedValue([
      { staff_id: 1, staff_name: "Chandran", is_active: true, created_at: "2026-06-23T00:00:00Z" },
      { staff_id: 2, staff_name: "Jayapal", is_active: true, created_at: "2026-06-23T00:00:00Z" },
    ]),
  },
  designsApi: {
    list: jest.fn().mockResolvedValue([
      { design_id: 1, size: "16X10", design_name: "16X10 Ridges", is_active: true, created_at: "2026-06-23T00:00:00Z" },
    ]),
    getGrades: jest.fn().mockResolvedValue([
      { grade_id: 1, grade_code: "1" },
    ]),
  },
}));

const mockCreate = jest.fn();
jest.mock("@/lib/api/transactions", () => ({
  salesApi: {
    create: (...args: unknown[]) => mockCreate(...args),
  },
}));

function renderWithQuery() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <SalesForm />
    </QueryClientProvider>
  );
}

beforeEach(() => {
  mockCreate.mockReset();
  mockCreate.mockResolvedValue({
    header_id: 1,
    sales_date: "2026-06-23",
    dealer_id: 1,
    place: "Dindivanam",
    loading_staff_id: 1,
    verified_by_id: 2,
    created_at: "2026-06-23T00:00:00Z",
    lines: [],
  });
});

describe("SalesForm", () => {
  test("TC-096: future sales_date blocks submit (zod ERR-001)", async () => {
    const { salesCreateSchema } = await import("@/lib/validation/transaction-schemas");
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const result = salesCreateSchema.safeParse({
      sales_date: tomorrow.toISOString().slice(0, 10),
      dealer_id: 1,
      loading_staff_id: 1,
      verified_by_id: 2,
      lines: [{ design_id: 1, grade_id: 1, nos: 5 }],
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(JSON.stringify(result.error.format())).toMatch(/future/i);
    }
  });

  test("TC-097: missing verified_by_id blocks submit", async () => {
    const user = userEvent.setup();
    renderWithQuery();
    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: /dealer/i })).toBeEnabled()
    );
    // Fill dealer + loading_staff + design + nos but leave verified_by blank
    await user.click(screen.getByRole("combobox", { name: /dealer/i }));
    await user.click(await screen.findByRole("option", { name: /Raj Hardwares/i }));
    await user.click(screen.getByRole("combobox", { name: /loading staff/i }));
    await user.click(await screen.findByRole("option", { name: /Chandran/i }));
    await user.click(screen.getByRole("combobox", { name: /^design$/i }));
    await user.click(await screen.findByRole("option", { name: /16X10 Ridges/i }));
    await waitFor(() =>
      expect(screen.getByText(/Grade 1/i)).toBeInTheDocument()
    );
    const nosInput = screen.getByLabelText(/Grade 1/i) as HTMLInputElement;
    await user.type(nosInput, "5");
    // submit without verified_by
    await user.click(screen.getByRole("button", { name: /Save Sale/i }));
    await waitFor(() => {
      expect(
        screen.getByText(/verified_by is required|Number must be greater than 0/i)
      ).toBeInTheDocument();
    });
    expect(mockCreate).not.toHaveBeenCalled();
  });
});
