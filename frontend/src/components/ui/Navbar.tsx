"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Cpu, Layers, Sparkles, FolderKanban, Settings } from "lucide-react";
import { BrutalBadge } from "@/components/ui/BrutalBadge";

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const [vramUsage, setVramUsage] = useState<string>("OK");

  const navItems = [
    { label: "Estudio Dual", href: "/", icon: Sparkles },
    { label: "Datasets & 3D", href: "/dataset", icon: FolderKanban },
    { label: "Ajustes & GPU", href: "/settings", icon: Settings },
  ];

  return (
    <header className="border-b-4 border-black bg-exon-card sticky top-0 z-50 px-6 py-3.5 shadow-brutal">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="bg-exon-orange p-2 border-2 border-black shadow-brutal-sm group-hover:rotate-3 transition-transform">
            <Layers className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="font-mono font-black text-xl tracking-tighter text-white">
              EXON<span className="text-exon-orange">-FACE</span>
            </span>
            <span className="text-[10px] block font-mono text-exon-lime font-bold tracking-widest uppercase">
              Neural 3D Engine
            </span>
          </div>
        </Link>

        {/* Links */}
        <nav className="flex items-center gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`px-4 py-2 border-2 border-black font-mono text-xs font-bold uppercase transition-all flex items-center gap-2 ${
                  isActive
                    ? "bg-exon-orange text-white shadow-brutal -translate-x-0.5 -translate-y-0.5"
                    : "bg-exon-panel text-slate-300 hover:bg-slate-700 hover:text-white"
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* GPU VRAM Badge */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 bg-exon-panel border-2 border-black px-3 py-1.5 shadow-brutal-sm">
            <Cpu className="w-4 h-4 text-exon-cyan" />
            <span className="text-xs font-mono font-bold text-slate-300">
              RTX 3070 8GB
            </span>
            <BrutalBadge variant="lime">ONLINE</BrutalBadge>
          </div>
        </div>
      </div>
    </header>
  );
};
