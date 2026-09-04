import React from "react";

interface BrutalButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "orange" | "lime" | "cyan" | "dark" | "outline";
  size?: "sm" | "md" | "lg";
  children: React.ReactNode;
}

export const BrutalButton: React.FC<BrutalButtonProps> = ({
  variant = "orange",
  size = "md",
  className = "",
  children,
  ...props
}) => {
  const baseStyles =
    "font-bold uppercase tracking-wider border-2 border-black transition-all duration-150 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none";

  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs shadow-brutal-sm hover:-translate-x-0.5 hover:-translate-y-0.5 active:translate-x-0 active:translate-y-0 active:shadow-none",
    md: "px-5 py-2.5 text-sm shadow-brutal hover:-translate-x-1 hover:-translate-y-1 active:translate-x-0 active:translate-y-0 active:shadow-none",
    lg: "px-8 py-3.5 text-base shadow-brutal-lg hover:-translate-x-1.5 hover:-translate-y-1.5 active:translate-x-0 active:translate-y-0 active:shadow-none",
  };

  const variantStyles = {
    orange: "bg-exon-orange text-white hover:bg-[#ff6a1f]",
    lime: "bg-exon-lime text-black hover:bg-[#d8ff33]",
    cyan: "bg-exon-cyan text-black hover:bg-[#33f3ff]",
    dark: "bg-exon-panel text-white hover:bg-slate-700",
    outline: "bg-transparent text-white border-white hover:bg-white hover:text-black",
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};
