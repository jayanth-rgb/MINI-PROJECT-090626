// S3 — TypeScript types mirroring backend Pydantic schemas in
// backend/src/presentation/schemas/reports.py (T-065).
// Frontend type names per UR-S3-001 convention (not DealerRead/TradingDesignRead).

export interface ConsolidationRow {
  design_id: number;
  design_name: string;
  size: string;
  grade_id: number;
  grade_code: string;
  total_nos: number;
}

export interface TransactionRow {
  sales_date: string; // ISO date YYYY-MM-DD
  dealer_id: number;
  dealer_name: string;
  place: string; // DS-013 snapshot value
  design_id: number;
  design_name: string;
  size: string;
  grade_id: number;
  grade_code: string;
  nos: number;
}

export interface SalesReportResponse {
  consolidation: ConsolidationRow[];
  transactions: TransactionRow[];
}

// All fields optional — each filter is independently optional (AC-046).
export interface SalesReportFilters {
  dateFrom?: string;   // ISO date YYYY-MM-DD
  dateTo?: string;     // ISO date YYYY-MM-DD
  dealerIds?: number[];
  places?: string[];
  designIds?: number[];
}
