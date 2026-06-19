// TC-039 — SupplierForm rejects empty supplier_name on submit (AC-001).
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { SupplierForm } from "@/components/admin/suppliers/SupplierForm";

describe("SupplierForm", () => {
  it("tc039 blocks submit and shows error when supplier_name is empty", async () => {
    const onSubmit = jest.fn();
    const { container } = render(
      <SupplierForm
        defaultValues={{ supplier_name: "", place: "Mallur" }}
        onSubmit={onSubmit}
        formId="supplier-form"
      />
    );

    const form = container.querySelector("#supplier-form") as HTMLFormElement;
    fireEvent.submit(form);

    const error = await screen.findByText(/required|min/i);
    expect(error).toBeInTheDocument();
    await waitFor(() => expect(onSubmit).not.toHaveBeenCalled());
  });
});
