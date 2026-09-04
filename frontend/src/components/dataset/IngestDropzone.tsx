"use client";

import React, { useState } from "react";
import { UploadCloud, Image as ImageIcon, Sparkles, AlertCircle, Loader2 } from "lucide-react";
import { api } from "@/services/api";
import { useAppStore } from "@/stores/useAppStore";
import { BrutalCard } from "@/components/ui/BrutalCard";
import { BrutalButton } from "@/components/ui/BrutalButton";
import { BrutalSlider } from "@/components/ui/BrutalSlider";

export const IngestDropzone: React.FC = () => {
  const { fetchSubjects } = useAppStore();
  const [subjectId, setSubjectId] = useState("");
  const [name, setName] = useState("");
  const [minSharpness, setMinSharpness] = useState(80.0);
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selected = Array.from(e.target.files);
      setFiles(selected);
      const previewUrls = selected.map((f) => URL.createObjectURL(f));
      setPreviews(previewUrls);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subjectId.trim() || !name.trim() || files.length === 0) {
      setError("Por favor completa el ID, nombre y selecciona al menos una imagen.");
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      setUploadResult(null);

      const result = await api.ingestDataset(
        subjectId.trim(),
        name.trim(),
        minSharpness,
        files
      );

      setUploadResult(
        `¡Ingesta Exitosa! Procesadas: ${result.processed_count}, Caras Válidas: ${result.valid_faces_count}, Descartadas por borrosas: ${result.discarded_count}`
      );
      // Reset form
      setFiles([]);
      setPreviews([]);
      setSubjectId("");
      setName("");
      await fetchSubjects();
    } catch (err: any) {
      setError(err?.response?.data?.message || err?.message || "Error al procesar el dataset");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <BrutalCard accent="lime" className="space-y-5">
      <div className="border-b-2 border-black pb-2">
        <h3 className="font-mono font-black text-lg text-white uppercase flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-exon-lime" />
          Ingestar Nuevo Sujeto Multi-Ángulo
        </h3>
        <p className="text-xs text-slate-400 font-sans">
          Carga múltiples fotos de frente, 3/4 y perfil para construir el catálogo de identidad tridimensional.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-mono font-bold uppercase text-slate-300">
              ID del Sujeto (Único)
            </label>
            <input
              type="text"
              placeholder="ej. subj_elena_01"
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
              className="w-full bg-exon-panel border-2 border-black p-2 text-sm font-mono text-white focus:outline-none focus:border-exon-lime"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono font-bold uppercase text-slate-300">
              Nombre Completo
            </label>
            <input
              type="text"
              placeholder="ej. Elena Rostova"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-exon-panel border-2 border-black p-2 text-sm font-mono text-white focus:outline-none focus:border-exon-lime"
            />
          </div>
        </div>

        {/* Sharpness threshold slider */}
        <BrutalSlider
          label="Filtro de Nitidez Laplaciana Mínima"
          description="Descarta automáticamente fotos movidas o desenfocadas"
          value={minSharpness}
          min={10.0}
          max={300.0}
          step={5.0}
          accent="lime"
          onChange={setMinSharpness}
        />

        {/* File Dropzone */}
        <div className="border-2 border-dashed border-slate-600 hover:border-exon-lime p-6 text-center bg-exon-panel/40 transition-colors">
          <input
            type="file"
            multiple
            accept="image/png,image/jpeg,image/webp"
            id="file-upload"
            onChange={handleFileChange}
            className="hidden"
          />
          <label htmlFor="file-upload" className="cursor-pointer block space-y-2">
            <ImageIcon className="w-8 h-8 text-exon-lime mx-auto" />
            <p className="font-mono text-xs font-bold text-white uppercase">
              Haz clic para seleccionar fotos del sujeto
            </p>
            <p className="text-[11px] text-slate-400">
              Soporta PNG, JPEG, WebP (Recomendado 5 a 20 fotos en varios ángulos)
            </p>
          </label>
        </div>

        {/* Previews Grid */}
        {previews.length > 0 && (
          <div className="space-y-2">
            <span className="font-mono text-xs text-slate-300 font-bold">
              {previews.length} Fotos Seleccionadas:
            </span>
            <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2 max-h-40 overflow-y-auto p-2 bg-exon-panel border-2 border-black">
              {previews.map((url, i) => (
                <img
                  key={i}
                  src={url}
                  alt={`preview-${i}`}
                  className="w-full h-16 object-cover border border-black"
                />
              ))}
            </div>
          </div>
        )}

        {/* Status / Feedback alerts */}
        {error && (
          <div className="p-3 bg-red-950/80 border-2 border-red-600 text-red-200 text-xs font-mono flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {uploadResult && (
          <div className="p-3 bg-emerald-950/80 border-2 border-exon-lime text-exon-lime text-xs font-mono">
            {uploadResult}
          </div>
        )}

        <BrutalButton
          type="submit"
          variant="lime"
          size="lg"
          className="w-full"
          disabled={isUploading || files.length === 0}
        >
          {isUploading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" /> Procesando Poses 3D...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" /> Extraer Poses y Catalogar Sujeto
            </>
          )}
        </BrutalButton>
      </form>
    </BrutalCard>
  );
};
