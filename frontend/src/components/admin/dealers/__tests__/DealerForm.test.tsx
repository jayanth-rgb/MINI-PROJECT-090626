// TC-042 — DealerForm rejects empty dealer_name OR empty place (AC-007).
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { DealerForm } from "@/components/admin/dealers/DealerForm";

describe.each([
  { dealer_name: "", place: "Dindivanam", expectedField: "dealer_name" },
  { dealer_name: "Raj", place: "", expectedField: "place" },
])("DealerForm validation: %p", ({ dealer_name, place, expectedField }) => {
  it("tc042 blocks submit when " + expectedField + " is empty", async () => {
    const onSubmit = jest.fn();
    const { container } = render(
      <DealerForm
        defaultValues={{ dealer_name, place }}
        onSubmit={onSubmit}
        formId="dealer-form"
      />
    );

    const form = container.querySelector("#dealer-form") as HTMLFormElement;
    fireEvent.submit(form);

    const error = await screen.findByText(/required|min/i);
    expect(error).toBeInTheDocument();
    await waitFor(() => expect(onSubmit).not.toHaveBeenCalled());
  });
});
