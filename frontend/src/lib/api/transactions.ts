import type {
  InwardCreate,
  InwardRead,
  SalesCreate,
  SalesRead,
  AdjustmentCreate,
  AdjustmentRead,
  DesignGradeReadWithCb,
} from "@/types/transactions";
import { apiClient } from "@/lib/api/client";

// ────────────────────────────────────────────────────────────────────────────
// inwardApi — /api/v1/inward
// ────────────────────────────────────────────────────────────────────────────

export const inwardApi = {
  async create(payload: InwardCreate): Promise<InwardRead> {
    const { data } = await apiClient.post<InwardRead>("/inward", payload);
    return data;
  },

  async list(filters?: {
    date_from?: string;
    date_to?: string;
  }): Promise<InwardRead[]> {
    const { data } = await apiClient.get<InwardRead[]>("/inward", {
      params: filters,
    });
    return data;
  },
};

// ────────────────────────────────────────────────────────────────────────────
// salesApi — /api/v1/sales
// ────────────────────────────────────────────────────────────────────────────

export const salesApi = {
  async create(payload: SalesCreate): Promise<SalesRead> {
    const { data } = await apiClient.post<SalesRead>("/sales", payload);
    return data;
  },

  async list(filters?: {
    date_from?: string;
    date_to?: string;
    dealer_ids?: number[];
    design_ids?: number[];
  }): Promise<SalesRead[]> {
    const { data } = await apiClient.get<SalesRead[]>("/sales", {
      params: filters,
    });
    return data;
  },
};

// ────────────────────────────────────────────────────────────────────────────
// adjustmentsApi — /api/v1/adjustments
// ────────────────────────────────────────────────────────────────────────────

export const adjustmentsApi = {
  async create(payload: AdjustmentCreate): Promise<AdjustmentRead> {
    const { data } = await apiClient.post<AdjustmentRead>(
      "/adjustments",
      payload
    );
    return data;
  },
};

// ────────────────────────────────────────────────────────────────────────────
// designsTxApi — /api/v1/designs/{id}/grades-with-cb
// ────────────────────────────────────────────────────────────────────────────

export const designsTxApi = {
  async getGradesWithCb(
    designId: number,
    stockDate: string
  ): Promise<DesignGradeReadWithCb[]> {
    const { data } = await apiClient.get<DesignGradeReadWithCb[]>(
      `/designs/${designId}/grades-with-cb`,
      { params: { stock_date: stockDate } }
    );
    return data;
  },
};
