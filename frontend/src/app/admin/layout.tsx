// T-032 — Admin shell with left sidebar nav + responsive mobile Sheet.
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import {
  Truck,
  Users,
  Store,
  Tags,
  Palette,
  GitBranch,
  Layers,
  Menu,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface NavItem {
  label: string;
  href: string;
  icon: typeof Truck;
}

const NAV: NavItem[] = [
  { label: "Suppliers", href: "/admin/suppliers", icon: Truck },
  { label: "Staff", href: "/admin/staff", icon: Users },
  { label: "Dealers", href: "/admin/dealers", icon: Store },
  { label: "Grades", href: "/admin/grades", icon: Tags },
  { label: "Designs", href: "/admin/designs", icon: Palette },
  { label: "Design-Grade Map", href: "/admin/design-grade-map", icon: GitBranch },
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const linkClass = (href: string) =>
    cn(
      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all duration-200",
      pathname?.startsWith(href)
        ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
        : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
    );

  const sidebarContent = (
    <>
      <div className="p-6 border-b flex items-center gap-3">
        <Layers className="h-6 w-6" />
        <div>
          <div className="font-semibold">Jayanth Trading</div>
          <div className="text-xs text-muted-foreground">Tiles Management</div>
        </div>
      </div>
      <nav className="flex-1 flex flex-col gap-1 p-3">
        {NAV.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={linkClass(item.href)}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar (md+) */}
      <aside className="hidden md:flex w-64 fixed left-0 top-0 h-full border-r bg-sidebar text-sidebar-foreground flex-col">
        {sidebarContent}
      </aside>

      {/* Mobile top bar */}
      <header className="md:hidden fixed top-0 left-0 right-0 h-14 z-30 border-b bg-background flex items-center px-4 gap-3">
        <Button
          variant="ghost"
          size="icon"
          aria-label="Open navigation"
          onClick={() => setMobileOpen(true)}
        >
          <Menu className="h-5 w-5" />
        </Button>
        <span className="font-semibold">Jayanth Trading Tiles</span>
      </header>

      {/* Mobile slide-in drawer */}
      {mobileOpen && (
        <>
          <div
            className="md:hidden fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
          <aside className="md:hidden fixed left-0 top-0 z-50 h-full w-64 border-r bg-sidebar text-sidebar-foreground flex flex-col">
            <div className="absolute right-2 top-2">
              <Button
                variant="ghost"
                size="icon"
                aria-label="Close navigation"
                onClick={() => setMobileOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            {sidebarContent}
          </aside>
        </>
      )}

      {/* Main content area */}
      <main className="flex-1 md:ml-64 min-h-screen bg-background pt-14 md:pt-0">
        <div className="p-4 sm:p-6 lg:p-8 max-w-6xl">{children}</div>
      </main>
    </div>
  );
}
