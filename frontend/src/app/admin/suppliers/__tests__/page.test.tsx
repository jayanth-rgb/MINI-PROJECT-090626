// TC-040 — SuppliersPage Deactivate button calls suppliersApi.remove with row id.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn() },
}));

jest.mock("@/lib/api/masters", () => ({
  suppliersApi: {
    list: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    remove: jest.fn(),
  },
}));

import { suppliersApi } from "@/lib/api/masters";
import SuppliersPage from "@/app/admin/suppliers/page";

const SEED = [
  {
    supplier_id: 7,
    supplier_name: "Antony Tiles",
    place: "Kerala",
    is_active: true,
    created_at: "2026-06-18T00:00:00Z",
  },
];

function renderWithClient(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("SuppliersPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (suppliersApi.list as jest.Mock).mockResolvedValue(SEED);
    (suppliersApi.remove as jest.Mock).mockResolvedValue({
      ...SEED[0],
      is_active: false,
    });
  });

  it("tc040 deactivate button calls suppliersApi.remove with supplier_id 7", async () => {
    renderWithClient(<SuppliersPage />);

    await screen.findByText("Antony Tiles");
    const deactivateButtons = await screen.findAllByRole("button", {
      name: /deactivate/i,
    });
    fireEvent.click(deactivateButtons[0]);

    await waitFor(() => {
      expect(suppliersApi.remove).toHaveBeenCalledWith(7);
    });
  });
});
