import React from "react";

interface BrutalSliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  accent?: "orange" | "lime" | "cyan";
  onChange: (val: number) => void;
  description?: string;
}

export const BrutalSlider: React.FC<BrutalSliderProps> = ({
  label,
  value,
  min,
  max,
  step = 0.05,
  unit = "",
  accent = "orange",
  onChange,
  description,
}) => {
  const accentText = {
    orange: "text-exon-orange",
    lime: "text-exon-lime",
    cyan: "text-exon-cyan",
  };

  return (
    <div className="flex flex-col gap-1.5 p-3 bg-exon-panel border-2 border-black shadow-brutal-sm">
      <div className="flex items-center justify-between text-xs font-mono uppercase">
        <span className="font-bold text-slate-200">{label}</span>
        <span className={`font-black ${accentText[accent]}`}>
          {value.toFixed(2)}
          {unit}
        </span>
      </div>
      {description && (
        <p className="text-[11px] text-slate-400 leading-tight">{description}</p>
      )}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-2 bg-slate-900 appearance-none cursor-pointer accent-exon-orange border border-black focus:outline-none"
      />
      <div className="flex justify-between text-[10px] text-slate-500 font-mono">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
};
