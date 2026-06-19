# T-029 — QueryProvider

**Module:** M-006 · **Depends on:** — · **TC refs:** — · **AC:** —

## Implementation logic

```tsx
// frontend/src/lib/query/provider.tsx
"use client";

import { useState, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
          },
        },
      })
  );
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
```

## Constraints
- MUST be 'use client' — server components cannot host QueryClientProvider
- QueryClient held in useState — module-level instance leaks across requests in App Router

## Do not touch
Any other file.

## Success criteria
- **Manual:** Wrap root layout (T-031); `useQuery` calls in admin pages do not throw
- **Automated:** Exercised by TC-040 / TC-043 / TC-045
- **DoD:** Client memoised; provider exports `QueryProvider`

## Checkout prompt
*"QueryProvider — useState-memoised client, staleTime 30s."*
