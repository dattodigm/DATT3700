"use client";

import { useState, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import { cn, throttle } from "@/lib/utils";
import { RotateCcw, RotateCw, Pause } from "lucide-react";

interface MotorSliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  showDirection?: boolean;
  className?: string;
  disabled?: boolean;
}

export function MotorSlider({
  label,
  value,
  onChange,
  min = -255,
  max = 255,
  showDirection = true,
  className,
  disabled = false,
}: MotorSliderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const throttledOnChange = useRef(throttle(onChange, 50)).current;

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = parseInt(e.target.value);
      throttledOnChange(newValue);
    },
    [throttledOnChange]
  );

  const handleQuickSet = (val: number) => {
    onChange(val);
  };

  // Calculate progress for visual feedback
  const progress = ((value - min) / (max - min)) * 100;
  const isReverse = value < 0;
  const isForward = value > 0;
  const isStopped = value === 0;

  return (
    <div className={cn("space-y-3", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-foreground">{label}</span>
        <div className="flex items-center gap-2">
          {showDirection && (
            <span
              className={cn(
                "flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
                isReverse && "bg-amber-500/20 text-amber-400",
                isForward && "bg-primary/20 text-primary",
                isStopped && "bg-secondary text-muted-foreground"
              )}
            >
              {isReverse && (
                <>
                  <RotateCcw className="h-3 w-3" />
                  REV
                </>
              )}
              {isForward && (
                <>
                  <RotateCw className="h-3 w-3" />
                  FWD
                </>
              )}
              {isStopped && (
                <>
                  <Pause className="h-3 w-3" />
                  STOP
                </>
              )}
            </span>
          )}
          <span className="w-12 text-right font-mono text-sm text-muted-foreground">
            {value}
          </span>
        </div>
      </div>

      {/* Slider Track with Visualization */}
      <div className="relative">
        {/* Background Track */}
        <div className="h-8 rounded-lg bg-muted/50">
          {/* Center line */}
          <div className="absolute left-1/2 top-0 h-full w-0.5 -translate-x-1/2 bg-border" />

          {/* Progress fill */}
          <motion.div
            className={cn(
              "absolute top-0 h-full rounded-lg transition-colors",
              isReverse ? "bg-amber-500/30" : "bg-primary/30"
            )}
            style={{
              left: isReverse ? `${progress}%` : "50%",
              width: `${Math.abs(progress - 50)}%`,
            }}
          />
        </div>

        {/* Slider Input */}
        <input
          type="range"
          min={min}
          max={max}
          value={value}
          onChange={handleChange}
          onMouseDown={() => setIsDragging(true)}
          onMouseUp={() => setIsDragging(false)}
          onTouchStart={() => setIsDragging(true)}
          onTouchEnd={() => setIsDragging(false)}
          disabled={disabled}
          className={cn(
            "absolute inset-0 h-8 w-full cursor-pointer appearance-none bg-transparent",
            disabled && "cursor-not-allowed opacity-50"
          )}
          style={{
            // Custom thumb styling
            WebkitAppearance: "none",
          }}
        />

        {/* Current value indicator */}
        <motion.div
          className={cn(
            "pointer-events-none absolute top-1/2 h-6 w-6 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 transition-colors",
            isDragging
              ? "border-primary bg-primary shadow-lg shadow-primary/30"
              : "border-primary/70 bg-card",
            disabled && "opacity-50"
          )}
          style={{ left: `${progress}%` }}
          animate={{ scale: isDragging ? 1.1 : 1 }}
        />
      </div>

      {/* Quick Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => handleQuickSet(-255)}
          disabled={disabled}
          className={cn(
            "flex flex-1 items-center justify-center gap-1 rounded-lg bg-amber-500/10 px-3 py-1.5 text-xs font-medium text-amber-400 transition-colors hover:bg-amber-500/20",
            disabled && "cursor-not-allowed opacity-50"
          )}
        >
          <RotateCcw className="h-3 w-3" />
          Full Rev
        </button>
        <button
          onClick={() => handleQuickSet(0)}
          disabled={disabled}
          className={cn(
            "flex flex-1 items-center justify-center gap-1 rounded-lg bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground transition-colors hover:bg-secondary/80",
            disabled && "cursor-not-allowed opacity-50"
          )}
        >
          <Pause className="h-3 w-3" />
          Stop
        </button>
        <button
          onClick={() => handleQuickSet(255)}
          disabled={disabled}
          className={cn(
            "flex flex-1 items-center justify-center gap-1 rounded-lg bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/20",
            disabled && "cursor-not-allowed opacity-50"
          )}
        >
          <RotateCw className="h-3 w-3" />
          Full Fwd
        </button>
      </div>
    </div>
  );
}
