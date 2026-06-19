# T-027 — Axios Client

**Module:** M-006 · **Depends on:** — · **TC refs:** — · **AC:** —

## Implementation logic

```ts
// frontend/src/lib/api/client.ts
import axios, { AxiosError } from "axios";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const status = error.response?.status ?? 0;
    const message =
      error.response?.data?.detail ??
      error.message ??
      "Unknown error";
    return Promise.reject({ status, message });
  }
);
```

## Constraints
- DS-010: NEXT_PUBLIC_API_URL must point at backend `/api/v1` base; we do not prepend it here, only baseURL
- Error shape consumed by toast handlers in T-038, T-040 (AC-011, AC-016)

## Do not touch
Any other file.

## Success criteria
- **Manual:** `import { apiClient } from "@/lib/api/client"` resolves
- **Automated:** Verified indirectly by TC-043 / TC-045 which mock axios responses
- **DoD:** Default export + named export; interceptor rejects with {status, message}

## Checkout prompt
*"Axios client — baseURL from NEXT_PUBLIC_API_URL + normalised error interceptor."*
