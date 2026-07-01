// TC-164, TC-165 — ReconciliationBadge (F-011, AC-050) unit + edge tests.
import { render, screen } from "@testing-library/react";
import { ReconciliationBadge } from "@/components/admin/reports/ReconciliationBadge";

test("test_tc164_reconciled_badge_displayed_when_sums_equal", () => {
  render(<ReconciliationBadge consolidationSum={537} transactionsSum={537} />);
  const badge = screen.getByRole("status");
  expect(badge).toHaveTextContent("Reconciled");
  expect(badge).toHaveTextContent("537");
  // aria-live must be present for AC-050 screen-reader announcement
  expect(badge).toHaveAttribute("aria-live", "polite");
});

test("test_tc165_mismatch_badge_displayed_when_sums_differ", () => {
  render(<ReconciliationBadge consolidationSum={537} transactionsSum={500} />);
  const badge = screen.getByRole("status");
  expect(badge).toHaveTextContent("Mismatch");
  expect(badge).toHaveTextContent("537");
  expect(badge).toHaveTextContent("500");
});
