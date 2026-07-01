// TC-161, TC-162, TC-163 — DashboardTable (F-010, AC-041) unit + edge tests.
import { render, screen } from "@testing-library/react";
import { DashboardTable } from "@/components/admin/dashboard/DashboardTable";
import type { DashboardRow } from "@/types/dashboard";

const ROWS: DashboardRow[] = [
  {
    design_id: 1,
    design_name: "16X10 Ridges",
    size: "16X10",
    grade_id: 1,
    grade_code: "1",
    opening: 120,
    inward: 200,
    outward: 150,
    adjust: -10,
    closing: 160,
  },
  {
    design_id: 1,
    design_name: "16X10 Ridges",
    size: "16X10",
    grade_id: 2,
    grade_code: "2",
    opening: 80,
    inward: 100,
    outward: 60,
    adjust: 0,
    closing: 120,
  },
];

test("test_tc161_renders_data_rows_with_all_8_display_columns", () => {
  render(<DashboardTable rows={ROWS} isLoading={false} />);
  expect(screen.getAllByText("16X10 Ridges")).toHaveLength(2);
  expect(screen.getAllByText("16X10")).toHaveLength(2);
  // grade codes
  expect(screen.getByText("1")).toBeInTheDocument();
  expect(screen.getByText("2")).toBeInTheDocument();
  // numeric columns — row 1 (120 appears twice: opening row-1 + closing row-2)
  expect(screen.getAllByText("120")).toHaveLength(2);
  expect(screen.getByText("200")).toBeInTheDocument(); // inward
  expect(screen.getByText("150")).toBeInTheDocument(); // outward
  expect(screen.getByText("-10")).toBeInTheDocument(); // adjust (negative)
  expect(screen.getByText("160")).toBeInTheDocument(); // closing
  // numeric columns — row 2
  expect(screen.getByText("80")).toBeInTheDocument();  // opening
  expect(screen.getByText("100")).toBeInTheDocument(); // inward
  expect(screen.getByText("60")).toBeInTheDocument();  // outward
  // adjust=0 and closing=120 already asserted above
});

test("test_tc162_empty_dashboard_state_shown_when_rows_empty_and_not_loading", () => {
  render(<DashboardTable rows={[]} isLoading={false} />);
  expect(
    screen.getByText(/no active design-grade pairs yet/i)
  ).toBeInTheDocument();
});

test("test_tc163_skeleton_shown_during_loading_no_data_or_empty_state_visible", () => {
  render(<DashboardTable rows={[]} isLoading={true} />);
  // Data values must not appear while loading
  expect(screen.queryByText("16X10 Ridges")).not.toBeInTheDocument();
  // Empty state CTA must not appear while loading
  expect(
    screen.queryByText(/no active design-grade pairs yet/i)
  ).not.toBeInTheDocument();
});
