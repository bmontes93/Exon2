"use client";

import React, { useState, useRef, useCallback } from "react";
import { MoveHorizontal } from "lucide-react";
import { BrutalBadge } from "@/components/ui/BrutalBadge";

interface SplitViewSliderProps {
  beforeImage: string;
  afterImage: string;
  beforeLabel?: string;
  afterLabel?: string;
}

export const SplitViewSlider: React.FC<SplitViewSliderProps> = ({
  beforeImage,
  afterImage,
  beforeLabel = "Original / Destino",
  afterLabel = "Síntesis EXON-FACE",
}) => {
  const [sliderPos, setSliderPos] = useState<number>(50);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef<boolean>(false);

  const handleMove = useCallback((clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const pos = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPos(pos);
  }, []);

  const handleMouseDown = () => {
    isDragging.current = true;
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging.current) {
      handleMove(e.clientX);
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches.length > 0) {
      handleMove(e.touches[0].clientX);
    }
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onTouchMove={handleTouchMove}
      className="relative w-full aspect-square max-h-[550px] border-4 border-black shadow-brutal-lg overflow-hidden select-none cursor-ew-resize bg-black"
    >
      {/* After Image (Full background) */}
      <img
        src={afterImage}
        alt="After synthesis"
        className="absolute inset-0 w-full h-full object-contain pointer-events-none"
      />
      <div className="absolute top-4 right-4 z-10 pointer-events-none">
        <BrutalBadge variant="orange">{afterLabel}</BrutalBadge>
      </div>

      {/* Before Image (Clipped using native CSS clip-path for 1:1 pixel perfect alignment) */}
      <img
        src={beforeImage}
        alt="Before target"
        className="absolute inset-0 w-full h-full object-contain pointer-events-none z-10"
        style={{
          clipPath: `inset(0 ${100 - sliderPos}% 0 0)`,
        }}
      />
      <div className="absolute top-4 left-4 z-20 pointer-events-none">
        <BrutalBadge variant="dark">{beforeLabel}</BrutalBadge>
      </div>

      {/* Divider Bar */}
      <div
        className="absolute top-0 bottom-0 w-1 bg-exon-orange z-30 pointer-events-none shadow-[0_0_10px_rgba(255,85,0,0.8)]"
        style={{ left: `calc(${sliderPos}% - 2px)` }}
      >
        {/* Central Drag Handle */}
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 bg-black border-2 border-exon-orange text-exon-orange p-1.5 shadow-brutal-sm">
          <MoveHorizontal className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
};
