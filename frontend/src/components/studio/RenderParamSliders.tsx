"use client";

import React from "react";
import { BrutalSlider } from "@/components/ui/BrutalSlider";
import { BrutalCard } from "@/components/ui/BrutalCard";
import { Sliders, Shield, Zap, Sparkles } from "lucide-react";

interface RenderParamsState {
  identityWeight: number;
  waveletHighPass: number;
  codeformerFidelity: number;
  occlusionMasking: boolean;
  sourceQuadrant: string;
}

interface RenderParamSlidersProps {
  params: RenderParamsState;
  onChange: (newParams: RenderParamsState) => void;
  availableQuadrants?: string[];
}

export const RenderParamSliders: React.FC<RenderParamSlidersProps> = ({
  params,
  onChange,
  availableQuadrants = [],
}) => {
  return (
    <BrutalCard accent="orange" className="space-y-4">
      <div className="flex items-center justify-between border-b-2 border-black pb-2">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-exon-orange" />
          <h4 className="font-mono font-black text-sm text-white uppercase">
            Ajuste Fino Studio Pro
          </h4>
        </div>
      </div>

      <div className="space-y-3">
        {/* Identity Weight Slider */}
        <BrutalSlider
          label="Fuerza de Identidad (Identity Weight)"
          description="Inyección vectorial ArcFace en el espacio latente generativo"
          value={params.identityWeight}
          min={0.1}
          max={1.8}
          step={0.05}
          accent="orange"
          onChange={(val) => onChange({ ...params, identityWeight: val })}
        />

        {/* Wavelet High-Pass Gain Slider */}
        <BrutalSlider
          label="Textura Wavelet (Anti-Plástico)"
          description="Retención y amplificación de poros, arrugas y grano de película"
          value={params.waveletHighPass}
          min={0.0}
          max={2.5}
          step={0.05}
          accent="lime"
          onChange={(val) => onChange({ ...params, waveletHighPass: val })}
        />

        {/* CodeFormer Fidelity Slider */}
        <BrutalSlider
          label="Fidelidad de Restauración (CodeFormer)"
          description="Balance entre super-resolución de ojos/dientes (0.0) y fidelidad de rasgos (1.0)"
          value={params.codeformerFidelity}
          min={0.1}
          max={1.0}
          step={0.05}
          accent="cyan"
          onChange={(val) => onChange({ ...params, codeformerFidelity: val })}
        />

        {/* Occlusion Segmentation Toggle */}
        <div className="flex items-center justify-between p-3 bg-exon-panel border-2 border-black">
          <div>
            <span className="text-xs font-mono font-bold uppercase text-slate-200 block">
              Segmentación de Oclusiones (BiSeNet)
            </span>
            <span className="text-[11px] text-slate-400">
              Preserva manos, dedos, gafas y cabello sobre la cara
            </span>
          </div>
          <button
            type="button"
            onClick={() =>
              onChange({
                ...params,
                occlusionMasking: !params.occlusionMasking,
              })
            }
            className={`w-12 h-6 border-2 border-black transition-colors p-0.5 flex items-center ${
              params.occlusionMasking
                ? "bg-exon-lime justify-end"
                : "bg-slate-800 justify-start"
            }`}
          >
            <div className="w-4 h-4 bg-black" />
          </button>
        </div>

        {/* Angle Quadrant Override */}
        {availableQuadrants.length > 0 && (
          <div className="space-y-1.5 p-3 bg-exon-panel border-2 border-black">
            <label className="text-xs font-mono font-bold uppercase text-slate-200 block">
              Forzar Cuadrante de Ángulo Fuente
            </label>
            <select
              value={params.sourceQuadrant}
              onChange={(e) =>
                onChange({ ...params, sourceQuadrant: e.target.value })
              }
              className="w-full bg-slate-900 border-2 border-black text-xs font-mono text-white p-2 focus:outline-none focus:border-exon-orange"
            >
              <option value="">Automático (Detectar ángulo destino)</option>
              {availableQuadrants.map((q) => (
                <option key={q} value={q}>
                  {q}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
    </BrutalCard>
  );
};
