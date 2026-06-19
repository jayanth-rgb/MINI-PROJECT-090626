// T-027 — Axios instance + normalised error interceptor.
//
// The interceptor surfaces FastAPI's `{detail: '...'}` HTTPException body as
// `{ status, detail }` (W-001 fix: prefer `detail` first — matches FastAPI
// register_error_handlers output).

import axios, { AxiosError } from "axios";

import type { ApiError } from "@/types/masters";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; message?: string }>) => {
    const status = error.response?.status ?? 0;
    const detail =
      error.response?.data?.detail ??
      error.response?.data?.message ??
      error.message ??
      "Request failed";
    const apiError: ApiError = { status, detail };
    return Promise.reject(apiError);
  }
);

export default apiClient;
