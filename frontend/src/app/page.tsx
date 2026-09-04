import React from "react";
import Link from "next/link";
import { Sparkles, FolderKanban, ShieldCheck, Zap, Layers3, Cpu } from "lucide-react";
import { BrutalCard } from "@/components/ui/BrutalCard";
import { BrutalButton } from "@/components/ui/BrutalButton";
import { BrutalBadge } from "@/components/ui/BrutalBadge";

export default function HomePage() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="bg-exon-card border-4 border-black p-8 shadow-brutal-lg relative overflow-hidden">
        <div className="absolute top-4 right-4 flex gap-2">
          <BrutalBadge variant="orange">V1.0.0 SDD</BrutalBadge>
          <BrutalBadge variant="lime">CUDA 12.X</BrutalBadge>
        </div>

        <div className="max-w-3xl space-y-4">
          <h1 className="text-4xl sm:text-5xl font-mono font-black tracking-tight text-white uppercase">
            Síntesis Neural <span className="text-exon-orange">3D</span> de Ultra-Fidelidad
          </h1>
          <p className="text-slate-300 text-sm sm:text-base font-sans leading-relaxed">
            Motor de intercambio facial de nueva generación optimizado para tu <strong className="text-exon-lime">RTX 3070 8GB</strong>.
            Supera el mapeo afín 2D tradicional mediante reconstrucción anatómica 3D, embeddings multi-ángulo, preservación de poros por frecuencias Wavelet y restauración facial CodeFormer.
          </p>

          <div className="pt-4 flex flex-wrap gap-4">
            <Link href="/studio">
              <BrutalButton variant="orange" size="lg">
                <Sparkles className="w-5 h-5" /> Entrar al Estudio Dual
              </BrutalButton>
            </Link>
            <Link href="/dataset">
              <BrutalButton variant="lime" size="lg">
                <FolderKanban className="w-5 h-5" /> Gestionar Datasets & 3D
              </BrutalButton>
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <BrutalCard accent="orange">
          <div className="flex items-center gap-3 mb-3">
            <Layers3 className="w-6 h-6 text-exon-orange" />
            <h3 className="font-mono font-black text-lg text-white uppercase">Mapeo 3D Real</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            Estimación de ángulos <span className="font-mono text-exon-orange">Yaw, Pitch, Roll</span> y landmarks 3DDFA para sintetizar caras consistentes incluso en perfiles extremos ($&gt;45^\circ$).
          </p>
        </BrutalCard>

        <BrutalCard accent="lime">
          <div className="flex items-center gap-3 mb-3">
            <Zap className="w-6 h-6 text-exon-lime" />
            <h3 className="font-mono font-black text-lg text-white uppercase">Wavelet Anti-Plástico</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            Descomposición en frecuencias altas y bajas. Transfiere los rasgos del sujeto reteniendo el grano de película, poros y micro-textura originales.
          </p>
        </BrutalCard>

        <BrutalCard accent="cyan">
          <div className="flex items-center gap-3 mb-3">
            <ShieldCheck className="w-6 h-6 text-exon-cyan" />
            <h3 className="font-mono font-black text-lg text-white uppercase">VRAM Guard 8GB</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            Orquestador secuencial determinista que administra la VRAM en la RTX 3070, asegurando picos inferiores a 7.0 GB sin cuelgues ni OOM.
          </p>
        </BrutalCard>
      </div>
    </div>
  );
}
