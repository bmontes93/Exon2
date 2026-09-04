"use client";

import React, { useRef, useState, useEffect } from "react";
import { Paintbrush, Eraser, RotateCcw, Eye } from "lucide-react";
import { BrutalButton } from "@/components/ui/BrutalButton";

interface MaskDrawingCanvasProps {
  imageSrc: string;
  onMaskChange?: (maskDataUrl: string) => void;
}

export const MaskDrawingCanvas: React.FC<MaskDrawingCanvasProps> = ({
  imageSrc,
  onMaskChange,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [brushSize, setBrushSize] = useState(25);
  const [isEraser, setIsEraser] = useState(false);
  const [showMask, setShowMask] = useState(true);

  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }, [imageSrc]);

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDrawing(true);
    draw(e);
  };

  const stopDrawing = () => {
    setIsDrawing(false);
    const canvas = canvasRef.current;
    if (canvas && onMaskChange) {
      onMaskChange(canvas.toDataURL("image/png"));
    }
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * canvas.width;
    const y = ((e.clientY - rect.top) / rect.height) * canvas.height;

    ctx.lineWidth = brushSize;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    if (isEraser) {
      ctx.globalCompositeOperation = "destination-out";
      ctx.strokeStyle = "rgba(0,0,0,1)";
    } else {
      ctx.globalCompositeOperation = "source-over";
      ctx.strokeStyle = "rgba(255, 85, 0, 0.65)"; // Neon orange mask tint
    }

    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const handleClear = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (onMaskChange) onMaskChange("");
  };

  return (
    <div className="space-y-3">
      {/* Controls toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 bg-exon-panel border-2 border-black">
        <div className="flex items-center gap-2">
          <BrutalButton
            type="button"
            size="sm"
            variant={!isEraser ? "orange" : "dark"}
            onClick={() => setIsEraser(false)}
          >
            <Paintbrush className="w-3.5 h-3.5" /> Pincel
          </BrutalButton>
          <BrutalButton
            type="button"
            size="sm"
            variant={isEraser ? "orange" : "dark"}
            onClick={() => setIsEraser(true)}
          >
            <Eraser className="w-3.5 h-3.5" /> Borrador
          </BrutalButton>
          <BrutalButton
            type="button"
            size="sm"
            variant="dark"
            onClick={() => setShowMask(!showMask)}
          >
            <Eye className="w-3.5 h-3.5" /> {showMask ? "Ocultar" : "Mostrar"}
          </BrutalButton>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-300">
            Radio: {brushSize}px
          </span>
          <input
            type="range"
            min="5"
            max="60"
            value={brushSize}
            onChange={(e) => setBrushSize(parseInt(e.target.value))}
            className="w-24 h-1.5 bg-black appearance-none cursor-pointer accent-exon-orange"
          />
          <BrutalButton type="button" size="sm" variant="dark" onClick={handleClear}>
            <RotateCcw className="w-3.5 h-3.5" /> Limpiar
          </BrutalButton>
        </div>
      </div>

      {/* Canvas over image layer */}
      <div className="relative w-full aspect-square max-h-[480px] bg-black border-4 border-black shadow-brutal overflow-hidden">
        <img
          src={imageSrc}
          alt="Target base"
          className="absolute inset-0 w-full h-full object-contain pointer-events-none"
        />
        <canvas
          ref={canvasRef}
          width={512}
          height={512}
          onMouseDown={startDrawing}
          onMouseUp={stopDrawing}
          onMouseMove={draw}
          onMouseLeave={stopDrawing}
          className={`absolute inset-0 w-full h-full object-contain cursor-crosshair ${
            !showMask ? "opacity-0" : "opacity-100"
          }`}
        />
      </div>
    </div>
  );
};
