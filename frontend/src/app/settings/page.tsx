"use client";

import React, { useEffect, useState } from "react";
import { useAppStore } from "@/stores/useAppStore";
import { api } from "@/services/api";
import { BrutalCard } from "@/components/ui/BrutalCard";
import { BrutalButton } from "@/components/ui/BrutalButton";
import { BrutalBadge } from "@/components/ui/BrutalBadge";
import { Settings, HardDrive, Cpu, Folder, Save, CheckCircle2, AlertCircle } from "lucide-react";

export default function SettingsPage() {
  const { systemStatus, fetchSystemStatus } = useAppStore();

  const [modelsDir, setModelsDir] = useState("");
  const [datasetsDir, setDatasetsDir] = useState("");
  const [outputsDir, setOutputsDir] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSystemStatus();
  }, [fetchSystemStatus]);

  useEffect(() => {
    if (systemStatus) {
      setModelsDir(systemStatus.models_dir);
      setDatasetsDir(systemStatus.datasets_dir);
      setOutputsDir(systemStatus.outputs_dir);
    }
  }, [systemStatus]);

  const handleSavePaths = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSaving(true);
      setError(null);
      setSaveSuccess(false);

      await api.updateSystemPaths({
        models_dir: modelsDir.trim() || undefined,
        datasets_dir: datasetsDir.trim() || undefined,
        outputs_dir: outputsDir.trim() || undefined,
      });

      setSaveSuccess(true);
      await fetchSystemStatus();
    } catch (err: any) {
      setError(err?.response?.data?.message || err?.message || "Error al actualizar las rutas");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b-4 border-black pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-mono font-black text-white uppercase flex items-center gap-3">
            <Settings className="w-8 h-8 text-exon-orange" />
            Configuración del Sistema & Hardware
          </h1>
          <p className="text-xs font-sans text-slate-400 mt-1">
            Administra los directorios de almacenamiento en disco y visualiza la telemetría de tu GPU NVIDIA RTX 3070.
          </p>
        </div>
      </div>

      {/* Hardware Diagnostics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* GPU VRAM Card */}
        <BrutalCard accent="cyan" className="space-y-4">
          <div className="flex items-center justify-between border-b-2 border-black pb-2">
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-exon-cyan" />
              <h3 className="font-mono font-black text-sm text-white uppercase">
                Memoria VRAM (CUDA)
              </h3>
            </div>
            <BrutalBadge variant="cyan">8 GB TOTAL</BrutalBadge>
          </div>

          <div className="space-y-2 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Asignada / En Uso:</span>
              <span className="text-exon-cyan font-bold">
                {systemStatus?.vram.allocated_mb.toFixed(1) || 0} MB
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Reservada:</span>
              <span className="text-slate-300 font-bold">
                {systemStatus?.vram.reserved_mb.toFixed(1) || 0} MB
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">VRAM Libre:</span>
              <span className="text-exon-lime font-bold">
                {systemStatus?.vram.free_mb.toFixed(1) || 8192} MB
              </span>
            </div>
          </div>
        </BrutalCard>

        {/* Disk Space Card */}
        <BrutalCard accent="lime" className="space-y-4">
          <div className="flex items-center justify-between border-b-2 border-black pb-2">
            <div className="flex items-center gap-2">
              <HardDrive className="w-5 h-5 text-exon-lime" />
              <h3 className="font-mono font-black text-sm text-white uppercase">
                Espacio en Disco Local
              </h3>
            </div>
            <BrutalBadge variant="lime">
              {systemStatus?.disk.free_gb || 0} GB LIBRES
            </BrutalBadge>
          </div>

          <div className="space-y-2 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Capacidad Total:</span>
              <span className="text-slate-200 font-bold">
                {systemStatus?.disk.total_gb || 0} GB
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Espacio Usado:</span>
              <span className="text-slate-300 font-bold">
                {systemStatus?.disk.used_gb || 0} GB
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Espacio Disponible:</span>
              <span className="text-exon-lime font-bold">
                {systemStatus?.disk.free_gb || 0} GB
              </span>
            </div>
          </div>
        </BrutalCard>
      </div>

      {/* Storage Paths Form */}
      <BrutalCard accent="orange" className="space-y-6">
        <div className="border-b-2 border-black pb-2">
          <h3 className="font-mono font-black text-lg text-white uppercase flex items-center gap-2">
            <Folder className="w-5 h-5 text-exon-orange" />
            Rutas de Almacenamiento en Disco (Configurables)
          </h3>
          <p className="text-xs text-slate-400 font-sans">
            Elige libremente en qué unidades o carpetas deseas guardar los pesos de modelos, datasets y renders.
          </p>
        </div>

        <form onSubmit={handleSavePaths} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-mono font-bold uppercase text-slate-300">
              Directorio de Modelos / Checkpoints (`MODEL_CACHE_DIR`)
            </label>
            <input
              type="text"
              value={modelsDir}
              onChange={(e) => setModelsDir(e.target.value)}
              className="w-full bg-exon-panel border-2 border-black p-2.5 text-sm font-mono text-white focus:outline-none focus:border-exon-orange"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono font-bold uppercase text-slate-300">
              Directorio de Datasets de Sujetos (`DATASET_DIR`)
            </label>
            <input
              type="text"
              value={datasetsDir}
              onChange={(e) => setDatasetsDir(e.target.value)}
              className="w-full bg-exon-panel border-2 border-black p-2.5 text-sm font-mono text-white focus:outline-none focus:border-exon-orange"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono font-bold uppercase text-slate-300">
              Directorio de Salidas y Renders (`OUTPUT_DIR`)
            </label>
            <input
              type="text"
              value={outputsDir}
              onChange={(e) => setOutputsDir(e.target.value)}
              className="w-full bg-exon-panel border-2 border-black p-2.5 text-sm font-mono text-white focus:outline-none focus:border-exon-orange"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-950/80 border-2 border-red-600 text-red-200 text-xs font-mono flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {saveSuccess && (
            <div className="p-3 bg-emerald-950/80 border-2 border-exon-lime text-exon-lime text-xs font-mono flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Rutas actualizadas y validadas con éxito.</span>
            </div>
          )}

          <BrutalButton
            type="submit"
            variant="orange"
            size="lg"
            className="w-full"
            disabled={isSaving}
          >
            <Save className="w-5 h-5" /> Guardar y Aplicar Nuevas Rutas
          </BrutalButton>
        </form>
      </BrutalCard>
    </div>
  );
}
