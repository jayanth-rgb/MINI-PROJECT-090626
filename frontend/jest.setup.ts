// Sprint S1 - jest test setup. Extends expect with @testing-library/jest-dom matchers.
import '@testing-library/jest-dom'

// Polyfill Element.scrollIntoView for jsdom — Radix Select calls it on focus
// and jsdom doesn't implement it. Needed for any test that opens a <Select>.
if (typeof Element !== 'undefined' && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = function () {}
}
