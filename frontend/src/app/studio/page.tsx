"use client";

import React, { useState, useEffect } from "react";
import { useAppStore } from "@/stores/useAppStore";
import { api, RenderJobResult } from "@/services/api";
import { BrutalCard } from "@/components/ui/BrutalCard";
import { BrutalButton } from "@/components/ui/BrutalButton";
import { BrutalBadge } from "@/components/ui/BrutalBadge";
import { SplitViewSlider } from "@/components/studio/SplitViewSlider";
import { MaskDrawingCanvas } from "@/components/studio/MaskDrawingCanvas";
import { RenderParamSliders } from "@/components/studio/RenderParamSliders";
import {
  Sparkles,
  Upload,
  Layers,
  Wand2,
  AlertCircle,
  Loader2,
  SlidersHorizontal,
  Zap,
} from "lucide-react";

export default function StudioPage() {
  const { subjects, selectedSubjectId, selectSubject, fetchSubjects } = useAppStore();

  const [mode, setMode] = useState<"EXPRESS" | "STUDIO_PRO">("EXPRESS");
  const [targetFile, setTargetFile] = useState<File | null>(null);
  const [targetPreview, setTargetPreview] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"split" | "mask">("split");
  const [isRendering, setIsRendering] = useState<boolean>(false);
  const [currentProgress, setCurrentProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<string>("");
  const [renderResult, setRenderResult] = useState<RenderJobResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [params, setParams] = useState({
    identityWeight: 1.0,
    waveletHighPass: 1.0,
    codeformerFidelity: 0.80,
    occlusionMasking: true,
    sourceQuadrant: "",
  });

  useEffect(() => {
    fetchSubjects();
  }, [fetchSubjects]);

  const selectedSubject = subjects.find((s) => s.subject_id === selectedSubjectId);

  const handleTargetFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setTargetFile(file);
      setTargetPreview(URL.createObjectURL(file));
      setRenderResult(null);
      setError(null);
    }
  };

  const [renderTimestamp, setRenderTimestamp] = useState<number>(Date.now());

  const handleExecuteRender = async () => {
    if (!selectedSubjectId) {
      setError("Por favor selecciona un sujeto del catálogo primero.");
      return;
    }
    if (!targetFile) {
      setError("Por favor sube una imagen destino donde colocar el rostro.");
      return;
    }

    let progInterval: any = null;
    try {
      setIsRendering(true);
      setError(null);
      setCurrentProgress(0.15);
      setCurrentStep("Detectando estructura 3D...");

      progInterval = setInterval(() => {
        setCurrentProgress((prev) => {
          if (prev < 0.3) { setCurrentStep("Detectando estructura 3D..."); return 0.35; }
          if (prev < 0.6) { setCurrentStep("Alineando landmarks con InSwapper..."); return 0.65; }
          if (prev < 0.8) { setCurrentStep("Inyectando identidad de Julio..."); return 0.82; }
          if (prev < 0.95) { setCurrentStep("Restauración GPEN & Wavelet..."); return 0.95; }
          return prev;
        });
      }, 1200);

      const result = await api.executeRender(
        selectedSubjectId,
        targetFile,
        mode,
        {
          identity_weight: params.identityWeight,
          wavelet_high_pass: params.waveletHighPass,
          codeformer_fidelity: params.codeformerFidelity,
          occlusion_masking: params.occlusionMasking,
          source_quadrant: params.sourceQuadrant || null,
        }
      );

      clearInterval(progInterval);
      setRenderResult(result);
      setRenderTimestamp(Date.now());
      setCurrentProgress(1.0);
      setCurrentStep("Síntesis Finalizada");
      setActiveTab("split");
    } catch (err: any) {
      if (progInterval) clearInterval(progInterval);
      setError(err?.response?.data?.message || err?.message || "Error durante el render");
    } finally {
      setIsRendering(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Studio Header & Mode Switch */}
      <div className="border-b-4 border-black pb-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-mono font-black text-white uppercase flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-exon-orange" />
            Estudio Dual de Síntesis Facial
          </h1>
          <p className="text-xs font-sans text-slate-400 mt-1">
            Reemplazo tridimensional de ultra-fidelidad con control de frecuencias Wavelet y máscara de oclusiones.
          </p>
        </div>

        {/* Dual Mode Switcher */}
        <div className="flex items-center gap-2 bg-exon-panel border-2 border-black p-1 shadow-brutal-sm">
          <button
            onClick={() => setMode("EXPRESS")}
            className={`px-4 py-2 font-mono text-xs font-bold uppercase transition-all flex items-center gap-1.5 ${
              mode === "EXPRESS"
                ? "bg-exon-lime text-black shadow-brutal-sm -translate-x-0.5 -translate-y-0.5"
                : "text-slate-300 hover:text-white"
            }`}
          >
            <Zap className="w-4 h-4" /> Modo Express (1-Click)
          </button>
          <button
            onClick={() => setMode("STUDIO_PRO")}
            className={`px-4 py-2 font-mono text-xs font-bold uppercase transition-all flex items-center gap-1.5 ${
              mode === "STUDIO_PRO"
                ? "bg-exon-orange text-white shadow-brutal-sm -translate-x-0.5 -translate-y-0.5"
                : "text-slate-300 hover:text-white"
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" /> Modo Studio Pro
          </button>
        </div>
      </div>

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Control Column (Subject + Target + Params) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Subject Picker */}
          <BrutalCard accent="lime" className="space-y-3">
            <label className="text-xs font-mono font-bold uppercase text-slate-300 block">
              1. Sujeto Fuente (Identidad a Inyectar)
            </label>
            <select
              value={selectedSubjectId || ""}
              onChange={(e) => selectSubject(e.target.value)}
              className="w-full bg-exon-panel border-2 border-black p-2.5 text-sm font-mono text-white focus:outline-none focus:border-exon-lime"
            >
              {subjects.length === 0 && <option value="">No hay sujetos registrados</option>}
              {subjects.map((s) => (
                <option key={s.subject_id} value={s.subject_id}>
                  {s.name} ({s.available_quadrants.length} Poses 3D)
                </option>
              ))}
            </select>
          </BrutalCard>

          {/* Target Image Dropzone */}
          <BrutalCard accent="orange" className="space-y-3">
            <label className="text-xs font-mono font-bold uppercase text-slate-300 block">
              2. Imagen Destino (Cualquier Ángulo / Expresión)
            </label>
            <div className="border-2 border-dashed border-slate-600 hover:border-exon-orange p-4 text-center bg-exon-panel/40 transition-colors">
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                id="target-upload"
                onChange={handleTargetFileChange}
                className="hidden"
              />
              <label htmlFor="target-upload" className="cursor-pointer block space-y-1.5">
                <Upload className="w-6 h-6 text-exon-orange mx-auto" />
                <p className="font-mono text-xs font-bold text-white uppercase">
                  Subir Foto Destino
                </p>
                <p className="text-[10px] text-slate-400">
                  PNG, JPEG o WebP de alta resolución
                </p>
              </label>
            </div>
          </BrutalCard>

          {/* Studio Pro Parameter Sliders (Only in STUDIO_PRO mode) */}
          {mode === "STUDIO_PRO" && (
            <RenderParamSliders
              params={params}
              onChange={setParams}
              availableQuadrants={selectedSubject?.available_quadrants}
            />
          )}

          {/* Render Action Button */}
          <BrutalButton
            variant={mode === "EXPRESS" ? "lime" : "orange"}
            size="lg"
            className="w-full text-lg py-4"
            disabled={isRendering || !targetFile || !selectedSubjectId}
            onClick={handleExecuteRender}
          >
            {isRendering ? (
              <>
                <Loader2 className="w-6 h-6 animate-spin" /> Renderizando Síntesis...
              </>
            ) : (
              <>
                <Wand2 className="w-6 h-6" />{" "}
                {mode === "EXPRESS" ? "Ejecutar Swap Express" : "Renderizar Síntesis Pro"}
              </>
            )}
          </BrutalButton>

          {/* Progress / Error alerts */}
          {isRendering && (
            <div className="p-4 bg-exon-card border-2 border-exon-orange space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="font-bold text-exon-orange uppercase">{currentStep}</span>
                <span className="font-black text-white">{Math.round(currentProgress * 100)}%</span>
              </div>
              <div className="w-full bg-black h-3 border border-black overflow-hidden">
                <div
                  className="bg-exon-orange h-full transition-all duration-300"
                  style={{ width: `${currentProgress * 100}%` }}
                />
              </div>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-950/80 border-2 border-red-600 text-red-200 text-xs font-mono flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Right Preview Column (Viewport & Comparators) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Tabs */}
          <div className="flex items-center gap-2 border-b-2 border-black pb-2">
            <button
              onClick={() => setActiveTab("split")}
              className={`px-4 py-2 font-mono text-xs font-bold uppercase transition-all ${
                activeTab === "split"
                  ? "bg-exon-orange text-white shadow-brutal-sm"
                  : "bg-exon-panel text-slate-400 hover:text-white"
              }`}
            >
              Comparador Split-Screen
            </button>
            {mode === "STUDIO_PRO" && targetPreview && (
              <button
                onClick={() => setActiveTab("mask")}
                className={`px-4 py-2 font-mono text-xs font-bold uppercase transition-all ${
                  activeTab === "mask"
                    ? "bg-exon-cyan text-black shadow-brutal-sm"
                    : "bg-exon-panel text-slate-400 hover:text-white"
                }`}
              >
                Pintor de Máscaras
              </button>
            )}
          </div>

          {/* Viewport content */}
          {activeTab === "split" && (
            <div>
              {targetPreview ? (
                <SplitViewSlider
                  beforeImage={targetPreview}
                  afterImage={
                    renderResult?.output_path
                      ? `http://127.0.0.1:8000/api/v1/outputs/${renderResult.output_path
                          .replace(/\\/g, "/")
                          .split("/")
                          .pop()}?t=${renderTimestamp}`
                      : targetPreview
                  }
                  afterLabel={renderResult ? "Síntesis EXON-FACE" : "Esperando Render..."}
                />
              ) : (
                <div className="aspect-square max-h-[550px] border-4 border-black bg-exon-card flex flex-col items-center justify-center text-slate-500 font-mono text-xs p-6 text-center shadow-brutal-lg">
                  <Layers className="w-12 h-12 text-slate-600 mb-3" />
                  <p className="font-bold uppercase text-slate-400">Visor de Comparación Vacío</p>
                  <p className="text-[11px] mt-1">
                    Carga una imagen destino a la izquierda para habilitar el comparador antes/después.
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === "mask" && targetPreview && (
            <div>
              <MaskDrawingCanvas imageSrc={targetPreview} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
