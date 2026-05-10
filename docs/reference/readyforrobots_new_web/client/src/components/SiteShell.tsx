import Footer from "@/components/Footer";
import Navbar from "@/components/Navbar";
import type { ReactNode } from "react";

type SiteShellProps = {
  children: ReactNode;
};

/**
 * Standard chrome for app-style pages (nav offset, footer).
 * Home uses its own full layout (hero + sections).
 */
export default function SiteShell({ children }: SiteShellProps) {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Navbar />
      <main className="flex-1 pt-16">{children}</main>
      <Footer />
    </div>
  );
}
