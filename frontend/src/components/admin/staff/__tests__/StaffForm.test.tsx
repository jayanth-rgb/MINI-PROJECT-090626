// TC-041 — StaffForm rejects empty staff_name on submit (AC-004).
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { StaffForm } from "@/components/admin/staff/StaffForm";

describe("StaffForm", () => {
  it("tc041 blocks submit and shows error when staff_name is empty", async () => {
    const onSubmit = jest.fn();
    const { container } = render(
      <StaffForm
        defaultValues={{ staff_name: "" }}
        onSubmit={onSubmit}
        formId="staff-form"
      />
    );

    const form = container.querySelector("#staff-form") as HTMLFormElement;
    fireEvent.submit(form);

    const error = await screen.findByText(/required|min/i);
    expect(error).toBeInTheDocument();
    await waitFor(() => expect(onSubmit).not.toHaveBeenCalled());
  });
});
