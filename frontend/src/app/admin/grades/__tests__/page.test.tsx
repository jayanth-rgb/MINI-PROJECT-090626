// TC-043 — GradesPage surfaces destructive toast on 409 duplicate grade_code.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn() },
}));

jest.mock("@/lib/api/masters", () => ({
  gradesApi: {
    list: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    remove: jest.fn(),
  },
}));

import { toast } from "sonner";
import { gradesApi } from "@/lib/api/masters";
import GradesPage from "@/app/admin/grades/page";

function renderWithClient(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("GradesPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (gradesApi.list as jest.Mock).mockResolvedValue([]);
    (gradesApi.create as jest.Mock).mockRejectedValue({
      status: 409,
      detail: "grade_code already exists",
    });
  });

  it("tc043 shows destructive toast containing 'grade_code' on 409", async () => {
    renderWithClient(<GradesPage />);

    const addButton = await screen.findByRole("button", { name: /add|new|create/i });
    fireEvent.click(addButton);

    const codeInput = await screen.findByLabelText(/grade.*code/i);
    fireEvent.change(codeInput, { target: { value: "1" } });

    const saveButton = await screen.findByRole("button", { name: /save|submit|create/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled();
    });
    const msg = (toast.error as jest.Mock).mock.calls[0][0];
    expect(String(msg)).toMatch(/grade_code/);
  });
});
