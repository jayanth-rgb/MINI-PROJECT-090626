// T-031 — Root Next.js App Router layout.
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Inter } from "next/font/google";

import "./globals.css";
import { QueryProvider } from "@/lib/query/provider";
import { Toaster } from "@/components/ui/sonner";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Jayanth Trading Tiles",
  description: "Trading tiles management system — master data administration",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-background font-sans antialiased">
        <QueryProvider>
          {children}
          <Toaster richColors closeButton position="top-right" />
        </QueryProvider>
      </body>
    </html>
  );
}
