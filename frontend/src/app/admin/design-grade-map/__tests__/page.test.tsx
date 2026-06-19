// TC-045 — DesignGradeMapPage surfaces destructive toast on 409 duplicate pair.
//
// We mock the form component so the test focuses on the page's mutation/toast
// behavior, not Radix Select portal mechanics (which are hard to drive in
// jsdom). The TC's assertion is about the toast surface, not the form UI.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn() },
}));

jest.mock("@/lib/api/masters", () => ({
  designGradeMapApi: {
    list: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    remove: jest.fn(),
  },
  designsApi: { list: jest.fn() },
  gradesApi: { list: jest.fn() },
}));

// Replace the real Radix-Select-driven form with a tiny form that submits a
// fixed payload, so the test exercises the mutation path deterministically.
jest.mock(
  "@/components/admin/design-grade-map/DesignGradeMapForm",
  () => ({
    DesignGradeMapForm: ({
      onSubmit,
      formId,
    }: {
      onSubmit: (v: { design_id: number; grade_id: number }) => void;
      formId: string;
    }) => (
      <form
        id={formId}
        data-testid="mock-dgm-form"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit({ design_id: 10, grade_id: 1 });
        }}
      />
    ),
  })
);

import { toast } from "sonner";
import {
  designGradeMapApi,
  designsApi,
  gradesApi,
} from "@/lib/api/masters";
import DesignGradeMapPage from "@/app/admin/design-grade-map/page";

function renderWithClient(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("DesignGradeMapPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (designGradeMapApi.list as jest.Mock).mockResolvedValue([]);
    (designsApi.list as jest.Mock).mockResolvedValue([
      {
        design_id: 10,
        size: "16X10",
        design_name: "16X10 Ridges",
        is_active: true,
        created_at: "2026-06-18T00:00:00Z",
      },
    ]);
    (gradesApi.list as jest.Mock).mockResolvedValue([
      { grade_id: 1, grade_code: "1", is_active: true },
    ]);
    (designGradeMapApi.create as jest.Mock).mockRejectedValue({
      status: 409,
      detail: "(design_id, grade_id) already exists",
    });
  });

  it("tc045 shows destructive toast containing 'exists' on 409", async () => {
    renderWithClient(<DesignGradeMapPage />);

    const addButton = await screen.findByRole("button", { name: /add|new|create/i });
    fireEvent.click(addButton);

    const mockForm = await screen.findByTestId("mock-dgm-form");
    fireEvent.submit(mockForm);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled();
    });
    const msg = (toast.error as jest.Mock).mock.calls[0][0];
    expect(String(msg)).toMatch(/exists/);
  });
});
