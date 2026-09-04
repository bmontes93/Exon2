"use client";

import React, { useEffect } from "react";
import { useAppStore } from "@/stores/useAppStore";
import { IngestDropzone } from "@/components/dataset/IngestDropzone";
import { SubjectCard } from "@/components/dataset/SubjectCard";
import { AngleGridVisualizer } from "@/components/dataset/AngleGridVisualizer";
import { BrutalCard } from "@/components/ui/BrutalCard";
import { FolderKanban, Users, AlertCircle } from "lucide-react";

export default function DatasetPage() {
  const {
    subjects,
    selectedSubjectId,
    selectSubject,
    fetchSubjects,
    isLoading,
    error,
  } = useAppStore();

  useEffect(() => {
    fetchSubjects();
  }, [fetchSubjects]);

  const selectedSubject = subjects.find(
    (s) => s.subject_id === selectedSubjectId
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-b-4 border-black pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-mono font-black text-white uppercase flex items-center gap-3">
            <FolderKanban className="w-8 h-8 text-exon-lime" />
            Catálogo de Sujetos & Reconstrucción 3D
          </h1>
          <p className="text-xs font-sans text-slate-400 mt-1">
            Gestiona los bancos de identidades vectoriales multi-ángulo indexados para síntesis facial.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Ingestion Dropzone */}
        <div className="lg:col-span-6 space-y-6">
          <IngestDropzone />
        </div>

        {/* Right Column: Catalog List & 3D Visualizer */}
        <div className="lg:col-span-6 space-y-6">
          {/* Active 3D Angle Compass */}
          {selectedSubject && (
            <AngleGridVisualizer
              coveredQuadrants={selectedSubject.available_quadrants}
            />
          )}

          {/* Subjects List */}
          <BrutalCard accent="orange" className="space-y-4">
            <div className="flex items-center justify-between border-b-2 border-black pb-2">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-exon-orange" />
                <h3 className="font-mono font-black text-sm text-white uppercase">
                  Sujetos Registrados ({subjects.length})
                </h3>
              </div>
            </div>

            {isLoading && (
              <p className="text-xs font-mono text-slate-400 py-4 text-center">
                Cargando catálogo...
              </p>
            )}

            {error && (
              <div className="p-3 bg-red-950/80 border-2 border-red-600 text-red-200 text-xs font-mono flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {!isLoading && subjects.length === 0 && (
              <div className="text-center py-8 text-slate-500 font-mono text-xs">
                No hay sujetos registrados aún. Utiliza el formulario de la izquierda para ingestar tu primer sujeto.
              </div>
            )}

            <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
              {subjects.map((subj) => (
                <SubjectCard
                  key={subj.subject_id}
                  subject={subj}
                  isSelected={subj.subject_id === selectedSubjectId}
                  onSelect={() => selectSubject(subj.subject_id)}
                />
              ))}
            </div>
          </BrutalCard>
        </div>
      </div>
    </div>
  );
}
