// TC-169, TC-170 — MultiSelectComboboxFallback (TD-010 closure, F-011).
//
// jsdom cannot drive Radix Popover internals; the Fallback native <select multiple>
// shares the same value-contract so its value-coercion logic (numeric IDs → number,
// string values → string unchanged) can be fully asserted here.
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MultiSelectComboboxFallback } from "@/components/ui/MultiSelectCombobox";

const DEALER_OPTIONS = [
  { value: 1, label: "Raj Hardwares" },
  { value: 2, label: "Tiles Mart" },
  { value: 3, label: "Shanmugam & Co" },
];

test("test_tc169_selects_numeric_option_and_emits_number_in_array", async () => {
  const onChange = jest.fn();
  render(
    <MultiSelectComboboxFallback
      options={DEALER_OPTIONS}
      value={[]}
      onChange={onChange}
      placeholder="Select dealers"
    />
  );
  const select = screen.getByRole("listbox");
  await userEvent.selectOptions(select, "1");
  // Numeric string "1" must be coerced back to number 1 per MultiSelectComboboxFallback contract
  expect(onChange).toHaveBeenCalledWith([1]);
});

test("test_tc170_selects_string_option_and_emits_string_value_unchanged", async () => {
  const onChange = jest.fn();
  const PLACE_OPTIONS = [
    { value: "Dindivanam", label: "Dindivanam" },
    { value: "Attibelle", label: "Attibelle" },
    { value: "Coimbatore", label: "Coimbatore" },
  ];
  render(
    <MultiSelectComboboxFallback
      options={PLACE_OPTIONS}
      value={[]}
      onChange={onChange}
      placeholder="Select places"
    />
  );
  const select = screen.getByRole("listbox");
  await userEvent.selectOptions(select, "Dindivanam");
  // String value must pass through without numeric coercion
  expect(onChange).toHaveBeenCalledWith(["Dindivanam"]);
});
