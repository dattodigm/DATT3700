"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { motion } from "framer-motion";
import { cn, clamp, throttle } from "@/lib/utils";
import { Crosshair, RotateCcw } from "lucide-react";

interface XYPadProps {
  label: string;
  x: number;
  y: number;
  onChange: (x: number, y: number) => void;
  xMin?: number;
  xMax?: number;
  yMin?: number;
  yMax?: number;
  xLabel?: string;
  yLabel?: string;
  size?: number;
  disabled?: boolean;
  className?: string;
  invertY?: boolean;
}

export function XYPad({
  label,
  x,
  y,
  onChange,
  xMin = -255,
  xMax = 255,
  yMin = -255,
  yMax = 255,
  xLabel = "X",
  yLabel = "Y",
  size = 200,
  disabled = false,
  className,
  invertY = false,
}: XYPadProps) {
  const padRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const throttledOnChange = useRef(throttle(onChange, 30)).current;

  // Convert value to position (0-1)
  const xPos = (x - xMin) / (xMax - xMin);
  const yPos = invertY
    ? (y - yMin) / (yMax - yMin)
    : 1 - (y - yMin) / (yMax - yMin);

  const handleInteraction = useCallback(
    (clientX: number, clientY: number) => {
      if (!padRef.current || disabled) return;

      const rect = padRef.current.getBoundingClientRect();
      const normalizedX = clamp((clientX - rect.left) / rect.width, 0, 1);
      const normalizedY = clamp((clientY - rect.top) / rect.height, 0, 1);

      const newX = Math.round(normalizedX * (xMax - xMin) + xMin);
      const newY = Math.round(
        (invertY ? normalizedY : 1 - normalizedY) * (yMax - yMin) + yMin
      );

      throttledOnChange(newX, newY);
    },
    [xMin, xMax, yMin, yMax, invertY, disabled, throttledOnChange]
  );

  const handleMouseDown = (e: React.MouseEvent) => {
    if (disabled) return;
    setIsDragging(true);
    handleInteraction(e.clientX, e.clientY);
  };

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging) return;
      handleInteraction(e.clientX, e.clientY);
    },
    [isDragging, handleInteraction]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleTouchStart = (e: React.TouchEvent) => {
    if (disabled) return;
    setIsDragging(true);
    const touch = e.touches[0];
    handleInteraction(touch.clientX, touch.clientY);
  };

  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (!isDragging) return;
      const touch = e.touches[0];
      handleInteraction(touch.clientX, touch.clientY);
    },
    [isDragging, handleInteraction]
  );

  const handleTouchEnd = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
      window.addEventListener("touchmove", handleTouchMove);
      window.addEventListener("touchend", handleTouchEnd);
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
      window.removeEventListener("touchmove", handleTouchMove);
      window.removeEventListener("touchend", handleTouchEnd);
    };
  }, [isDragging, handleMouseMove, handleMouseUp, handleTouchMove, handleTouchEnd]);

  const handleReset = () => {
    const centerX = Math.round((xMax + xMin) / 2);
    const centerY = Math.round((yMax + yMin) / 2);
    onChange(centerX, centerY);
  };

  return (
    <div className={cn("space-y-3", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-foreground">{label}</span>
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-muted-foreground">
            {xLabel}: {x} | {yLabel}: {y}
          </span>
          <button
            onClick={handleReset}
            disabled={disabled}
            className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            title="Reset to center"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* XY Pad */}
      <div
        ref={padRef}
        className={cn(
          "control-pad relative cursor-crosshair select-none",
          disabled && "cursor-not-allowed opacity-50"
        )}
        style={{ width: size, height: size }}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
      >
        {/* Grid */}
        <div className="control-pad-grid" />

        {/* Center lines */}
        <div className="control-pad-center" />
        <div className="control-pad-center-h" />

        {/* Axis labels */}
        <span className="absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] text-muted-foreground">
          +{yLabel}
        </span>
        <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[10px] text-muted-foreground">
          -{yLabel}
        </span>
        <span className="absolute -left-5 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground">
          -{xLabel}
        </span>
        <span className="absolute -right-5 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground">
          +{xLabel}
        </span>

        {/* Position indicator */}
        <motion.div
          className={cn(
            "pointer-events-none absolute flex items-center justify-center",
            isDragging && "z-10"
          )}
          style={{
            left: `${xPos * 100}%`,
            top: `${yPos * 100}%`,
            transform: "translate(-50%, -50%)",
          }}
          animate={{
            scale: isDragging ? 1.2 : 1,
          }}
          transition={{ duration: 0.1 }}
        >
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full border-2 transition-colors",
              isDragging
                ? "border-primary bg-primary/20 shadow-lg shadow-primary/30"
                : "border-primary/50 bg-card/80"
            )}
          >
            <Crosshair className="h-4 w-4 text-primary" />
          </div>
        </motion.div>
      </div>
    </div>
  );
}
