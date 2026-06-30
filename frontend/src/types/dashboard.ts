// S3 — TypeScript types mirroring backend Pydantic schema in
// backend/src/presentation/schemas/dashboard.py (T-064).
// 10 fields exactly matching the DashboardRow Pydantic model.

export interface DashboardRow {
  design_id: number;
  design_name: string;
  size: string;
  grade_id: number;
  grade_code: string;
  opening: number;
  inward: number;
  outward: number;
  adjust: number;
  closing: number;
}
