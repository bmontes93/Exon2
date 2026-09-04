import React from "react";
import { User, Calendar, CheckCircle } from "lucide-react";
import { SubjectProfile } from "@/services/api";
import { BrutalCard } from "@/components/ui/BrutalCard";
import { BrutalBadge } from "@/components/ui/BrutalBadge";

interface SubjectCardProps {
  subject: SubjectProfile;
  isSelected: boolean;
  onSelect: () => void;
}

export const SubjectCard: React.FC<SubjectCardProps> = ({
  subject,
  isSelected,
  onSelect,
}) => {
  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer transition-all duration-150 ${
        isSelected ? "scale-[1.02]" : "hover:scale-[1.01]"
      }`}
    >
      <BrutalCard
        accent={isSelected ? "orange" : "none"}
        className={isSelected ? "bg-slate-900 ring-2 ring-exon-orange" : ""}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-exon-panel p-2.5 border-2 border-black">
              <User className="w-5 h-5 text-exon-orange" />
            </div>
            <div>
              <h4 className="font-mono font-black text-base text-white">
                {subject.name}
              </h4>
              <p className="font-mono text-xs text-slate-400">
                ID: {subject.subject_id}
              </p>
            </div>
          </div>
          {isSelected && (
            <BrutalBadge variant="orange">SELECCIONADO</BrutalBadge>
          )}
        </div>

        <div className="mt-4 pt-3 border-t-2 border-black flex items-center justify-between text-xs font-mono text-slate-400">
          <div className="flex items-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5 text-exon-lime" />
            <span>{subject.available_quadrants.length} Poses 3D</span>
          </div>
          <div className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span>{new Date(subject.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </BrutalCard>
    </div>
  );
};
