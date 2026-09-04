import React from "react";
import { CheckCircle2, XCircle, Compass } from "lucide-react";
import { BrutalCard } from "@/components/ui/BrutalCard";

interface AngleGridVisualizerProps {
  coveredQuadrants: string[];
}

const ALL_QUADRANTS = [
  { id: "FRONTAL", label: "Frontal (0°)", desc: "Vista directa" },
  { id: "THREE_QUARTER_LEFT", label: "3/4 Izquierdo (-30°)", desc: "Semi-perfil izq" },
  { id: "THREE_QUARTER_RIGHT", label: "3/4 Derecho (+30°)", desc: "Semi-perfil der" },
  { id: "PROFILE_LEFT", label: "Perfil Izquierdo (-60°)", desc: "Perfil puro izq" },
  { id: "PROFILE_RIGHT", label: "Perfil Derecho (+60°)", desc: "Perfil puro der" },
  { id: "PITCH_UP", label: "Cenital / Arriba", desc: "Mirando arriba" },
  { id: "PITCH_DOWN", label: "Nadir / Abajo", desc: "Mirando abajo" },
];

export const AngleGridVisualizer: React.FC<AngleGridVisualizerProps> = ({
  coveredQuadrants,
}) => {
  return (
    <BrutalCard accent="cyan" className="space-y-4">
      <div className="flex items-center justify-between border-b-2 border-black pb-2">
        <div className="flex items-center gap-2">
          <Compass className="w-5 h-5 text-exon-cyan" />
          <h4 className="font-mono font-black text-sm text-white uppercase">
            Mapa de Cobertura 3D ($Yaw, Pitch$)
          </h4>
        </div>
        <span className="font-mono text-xs font-bold text-exon-cyan">
          {coveredQuadrants.length} / {ALL_QUADRANTS.length} Ángulos
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        {ALL_QUADRANTS.map((q) => {
          const isCovered = coveredQuadrants.includes(q.id);
          return (
            <div
              key={q.id}
              className={`p-2.5 border-2 border-black flex items-start gap-2.5 transition-colors ${
                isCovered
                  ? "bg-emerald-950/60 border-exon-lime text-slate-100"
                  : "bg-exon-panel/50 text-slate-500 opacity-60"
              }`}
            >
              {isCovered ? (
                <CheckCircle2 className="w-4 h-4 text-exon-lime shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" />
              )}
              <div className="text-xs">
                <p className="font-mono font-bold uppercase">{q.label}</p>
                <p className="text-[10px] text-slate-400 font-sans">{q.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </BrutalCard>
  );
};
