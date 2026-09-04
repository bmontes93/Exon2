import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/ui/Navbar";

export const metadata: Metadata = {
  title: "EXON-FACE — High-Fidelity 3D Face Synthesis Studio",
  description: "Advanced Neural Face Swapping & 3D Synthesis Studio for RTX 3070",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="bg-exon-dark text-slate-100 min-h-screen flex flex-col antialiased">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto p-6">{children}</main>
        <footer className="border-t-4 border-black bg-exon-card p-6 mt-12 text-center text-xs font-mono text-slate-500">
          EXON-FACE ENGINE • SPEC-DRIVEN DEVELOPMENT • DEVSECOPS COMPLIANT
        </footer>
      </body>
    </html>
  );
}
