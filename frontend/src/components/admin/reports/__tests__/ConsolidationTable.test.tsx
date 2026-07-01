// TC-167, TC-168 — ConsolidationTable (F-011, AC-047) unit + edge tests.
import { render, screen } from "@testing-library/react";
import { ConsolidationTable } from "@/components/admin/reports/ConsolidationTable";
import type { ConsolidationRow } from "@/types/reports";

const ROWS: ConsolidationRow[] = [
  {
    design_id: 1,
    design_name: "16X10 Ridges",
    size: "16X10",
    grade_id: 1,
    grade_code: "1",
    total_nos: 7,
  },
  {
    design_id: 1,
    design_name: "16X10 Ridges",
    size: "16X10",
    grade_id: 2,
    grade_code: "2",
    total_nos: 10,
  },
  {
    design_id: 2,
    design_name: "12X8 Ridges",
    size: "12X8",
    grade_id: 1,
    grade_code: "1",
    total_nos: 5,
  },
];

test("test_tc167_renders_consolidation_rows_and_footer_total_nos_sum", () => {
  render(<ConsolidationTable rows={ROWS} isLoading={false} />);
  // Row data
  expect(screen.getAllByText("16X10 Ridges")).toHaveLength(2);
  expect(screen.getByText("12X8 Ridges")).toBeInTheDocument();
  expect(screen.getByText("7")).toBeInTheDocument();
  expect(screen.getByText("10")).toBeInTheDocument();
  expect(screen.getByText("5")).toBeInTheDocument();
  // Footer: 7 + 10 + 5 = 22
  expect(screen.getByText("22")).toBeInTheDocument();
  // Footer label
  expect(screen.getByText("Total")).toBeInTheDocument();
});

test("test_tc168_empty_message_rendered_when_rows_empty_and_not_loading", () => {
  render(<ConsolidationTable rows={[]} isLoading={false} />);
  expect(screen.getByText(/no matching sales/i)).toBeInTheDocument();
  // Footer must not render when empty
  expect(screen.queryByText("Total")).not.toBeInTheDocument();
});
