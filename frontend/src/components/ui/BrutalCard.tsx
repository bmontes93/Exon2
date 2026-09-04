import React from "react";

interface BrutalCardProps extends React.HTMLAttributes<HTMLDivElement> {
  accent?: "none" | "orange" | "lime" | "cyan";
  children: React.ReactNode;
}

export const BrutalCard: React.FC<BrutalCardProps> = ({
  accent = "none",
  className = "",
  children,
  ...props
}) => {
  const accentBorders = {
    none: "border-black shadow-brutal",
    orange: "border-exon-orange shadow-brutal-orange",
    lime: "border-exon-lime shadow-brutal-lime",
    cyan: "border-exon-cyan shadow-brutal-cyan",
  };

  return (
    <div
      className={`bg-exon-card border-2 p-5 ${accentBorders[accent]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
