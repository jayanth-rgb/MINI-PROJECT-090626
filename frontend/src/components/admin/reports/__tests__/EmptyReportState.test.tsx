// TC-166 — EmptyReportState (F-011) — onClear callback invoked on button click.
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmptyReportState } from "@/components/admin/reports/EmptyReportState";

test("test_tc166_clear_filters_button_invokes_on_clear_callback", async () => {
  const onClear = jest.fn();
  render(<EmptyReportState onClear={onClear} />);
  const btn = screen.getByRole("button", { name: /clear all filters/i });
  expect(btn).toBeInTheDocument();
  await userEvent.click(btn);
  expect(onClear).toHaveBeenCalledTimes(1);
});
