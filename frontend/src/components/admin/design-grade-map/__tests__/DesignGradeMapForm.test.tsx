// TC-046 — DesignGradeMapForm blocks submit when neither dropdown is selected.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { DesignGradeMapForm } from "@/components/admin/design-grade-map/DesignGradeMapForm";

const DESIGNS = [
  {
    design_id: 10,
    size: "16X10",
    design_name: "16X10 Ridges",
    is_active: true,
    created_at: "2026-06-18T00:00:00Z",
  },
];

const GRADES = [{ grade_id: 1, grade_code: "1", is_active: true }];

describe("DesignGradeMapForm", () => {
  it("tc046 blocks submit and shows errors for design_id and grade_id when nothing is selected", async () => {
    const onSubmit = jest.fn();
    const { container } = render(
      <DesignGradeMapForm
        defaultValues={{}}
        designs={DESIGNS}
        grades={GRADES}
        onSubmit={onSubmit}
        formId="design-grade-map-form"
      />
    );

    const form = container.querySelector("#design-grade-map-form") as HTMLFormElement;
    fireEvent.submit(form);

    const errors = await screen.findAllByText(/required|positive|min|select/i);
    expect(errors.length).toBeGreaterThanOrEqual(2);
    await waitFor(() => expect(onSubmit).not.toHaveBeenCalled());
  });
});
