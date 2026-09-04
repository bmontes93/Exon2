import React from "react";

interface BrutalBadgeProps {
  variant?: "orange" | "lime" | "cyan" | "dark" | "red";
  children: React.ReactNode;
}

export const BrutalBadge: React.FC<BrutalBadgeProps> = ({
  variant = "orange",
  children,
}) => {
  const variantStyles = {
    orange: "bg-exon-orange text-white border-black",
    lime: "bg-exon-lime text-black border-black",
    cyan: "bg-exon-cyan text-black border-black",
    dark: "bg-exon-panel text-slate-300 border-black",
    red: "bg-red-600 text-white border-black",
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-xs font-mono font-bold uppercase tracking-wider border-2 shadow-brutal-sm ${variantStyles[variant]}`}
    >
      {children}
    </span>
  );
};
