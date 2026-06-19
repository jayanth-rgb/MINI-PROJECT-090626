# T-031 — Root Layout + Home Page

**Module:** M-006 · **Depends on:** T-029 · **TC refs:** — · **AC:** —

## Implementation logic

```tsx
// frontend/src/app/layout.tsx
import type { Metadata, ReactNode } from "react";
import "./globals.css";
import { QueryProvider } from "@/lib/query/provider";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "Jayanth Trading Tiles",
  description: "Trading tiles management system",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          {children}
          <Toaster />
        </QueryProvider>
      </body>
    </html>
  );
}
```

```tsx
// frontend/src/app/page.tsx
import { redirect } from "next/navigation";

export default function HomePage() {
  redirect("/admin/suppliers");
}
```

## Constraints
- Server component (HomePage) — no 'use client'
- Toaster from shadcn sonner registry is the source of toast notifications used in TC-043/TC-045

## Do not touch
Any other file.

## Success criteria
- **Manual:** Visit `/` -> auto-redirect to `/admin/suppliers`; browser tab reads "Jayanth Trading Tiles"
- **Automated:** No automated test
- **DoD:** layout + page exports correct

## Checkout prompt
*"Root layout (QueryProvider + Toaster) + home redirect."*
