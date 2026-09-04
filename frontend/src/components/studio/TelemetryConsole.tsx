"use client";

import React from "react";
import { Terminal, Cpu, Activity } from "lucide-react";
import { BrutalCard } from "@/components/ui/BrutalCard";
import { BrutalBadge } from "@/components/ui/BrutalBadge";

interface TelemetryConsoleProps {
  logs: string[];
  currentStep?: string;
  progress?: number;
  vramAllocatedMb?: number;
  isConnected?: boolean;
}

export const TelemetryConsole: React.FC<TelemetryConsoleProps> = ({
  logs,
  currentStep = "IDLE",
  progress = 0,
  vramAllocatedMb = 0,
  isConnected = false,
}) => {
  return (
    <BrutalCard accent="none" className="bg-black text-slate-200 font-mono space-y-3 p-4">
      {/* Console Header */}
      <div className="flex flex-wrap items-center justify-between border-b-2 border-slate-800 pb-2 gap-2">
        <div className="flex items-center gap-2 text-xs">
          <Terminal className="w-4 h-4 text-exon-orange" />
          <span className="font-bold uppercase tracking-wider text-white">
            Consola de Telemetría CUDA (RTX 3070)
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-slate-900 px-2 py-0.5 border border-slate-700 text-[11px]">
            <Cpu className="w-3.5 h-3.5 text-exon-cyan" />
            <span className="text-slate-300">VRAM:</span>
            <span className="font-bold text-exon-cyan">{vramAllocatedMb.toFixed(0)} MB</span>
          </div>

          <BrutalBadge variant={isConnected ? "lime" : "dark"}>
            {isConnected ? "STREAM ACTIVO" : "STANDBY"}
          </BrutalBadge>
        </div>
      </div>

      {/* Realtime Stage Bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-[11px]">
          <span className="text-slate-400">FASE ACTUAL: <strong className="text-exon-orange">{currentStep}</strong></span>
          <span className="text-exon-lime font-bold">{Math.round(progress * 100)}%</span>
        </div>
        <div className="w-full h-2 bg-slate-900 border border-slate-700 overflow-hidden">
          <div
            className="bg-exon-orange h-full transition-all duration-300"
            style={{ width: `${progress * 100}%` }}
          />
        </div>
      </div>

      {/* Terminal Logs Window */}
      <div className="bg-slate-950 p-3 border border-slate-800 h-32 overflow-y-auto text-[11px] space-y-1 font-mono">
        {logs.length === 0 ? (
          <p className="text-slate-600 italic">Esperando inicio de pipeline...</p>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="text-slate-300 flex items-start gap-2">
              <span className="text-exon-orange select-none">&gt;</span>
              <span>{log}</span>
            </div>
          ))
        )}
      </div>
    </BrutalCard>
  );
};
