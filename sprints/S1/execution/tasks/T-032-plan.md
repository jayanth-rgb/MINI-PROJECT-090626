# T-032 — Admin Shell Layout

**Module:** M-006 · **Depends on:** — · **TC refs:** — · **AC:** —

## Implementation logic

```tsx
// frontend/src/app/admin/layout.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/admin/suppliers", label: "Suppliers" },
  { href: "/admin/staff", label: "Staff" },
  { href: "/admin/dealers", label: "Dealers" },
  { href: "/admin/grades", label: "Grades" },
  { href: "/admin/designs", label: "Designs" },
  { href: "/admin/design-grade-map", label: "Design-Grade Map" },
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="flex min-h-screen">
      <aside className="w-60 border-r bg-muted/40 p-4">
        <h1 className="mb-4 text-lg font-semibold">Trading Tiles</h1>
        <nav className="flex flex-col gap-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded px-3 py-2 text-sm hover:bg-accent",
                pathname?.startsWith(item.href) && "bg-accent font-medium"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
```

## Constraints
- 'use client' — usePathname requires a client component
- Active highlight uses startsWith so deep paths still match parent

## Do not touch
Any other file.

## Success criteria
- **Manual:** Click between nav items; active item highlighted
- **Automated:** None
- **DoD:** Layout exports default AdminLayout

## Checkout prompt
*"Admin shell — sidebar with 6 nav items, active highlight via usePathname."*
