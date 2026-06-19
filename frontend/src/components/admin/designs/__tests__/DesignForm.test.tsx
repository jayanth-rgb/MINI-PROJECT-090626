// TC-044 — DesignForm rejects empty size OR empty design_name (AC-013).
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { DesignForm } from "@/components/admin/designs/DesignForm";

describe.each([
  { size: "", design_name: "16X10 Ridges", expectedField: "size" },
  { size: "16X10", design_name: "", expectedField: "design_name" },
])("DesignForm validation: %p", ({ size, design_name, expectedField }) => {
  it("tc044 blocks submit when " + expectedField + " is empty", async () => {
    const onSubmit = jest.fn();
    const { container } = render(
      <DesignForm
        defaultValues={{ size, design_name }}
        onSubmit={onSubmit}
        formId="design-form"
      />
    );

    const form = container.querySelector("#design-form") as HTMLFormElement;
    fireEvent.submit(form);

    const error = await screen.findByText(/required|min/i);
    expect(error).toBeInTheDocument();
    await waitFor(() => expect(onSubmit).not.toHaveBeenCalled());
  });
});
