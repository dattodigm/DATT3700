"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Zap, Play, Square } from "lucide-react";
import { cn } from "@/lib/utils";
import { MotorSlider } from "./motor-slider";
import { KAIT_MOTION_PRESETS } from "@/lib/types";

interface KaitPanelProps {
  deviceName: string;
  onMotorChange: (speed: number) => void;
  onMotionPreset: (mode: number) => void;
  onStop: () => void;
  disabled?: boolean;
}

export function KaitPanel({
  deviceName,
  onMotorChange,
  onMotionPreset,
  onStop,
  disabled = false,
}: KaitPanelProps) {
  const [motorSpeed, setMotorSpeed] = useState(0);
  const [activePreset, setActivePreset] = useState<number | null>(null);

  const handleMotorChange = (speed: number) => {
    setMotorSpeed(speed);
    onMotorChange(speed);
  };

  const handlePreset = (mode: number) => {
    setActivePreset(mode);
    onMotionPreset(mode);
    // Reset after preset duration
    const preset = KAIT_MOTION_PRESETS.find((p) => p.id === mode);
    if (preset) {
      setTimeout(() => setActivePreset(null), preset.duration);
    }
  };

  const handleStop = () => {
    setMotorSpeed(0);
    setActivePreset(null);
    onStop();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10">
          <Zap className="h-5 w-5 text-amber-400" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">Kait Motor Control</h3>
          <p className="text-xs text-muted-foreground">DC Motor with Motion Presets</p>
        </div>
      </div>

      {/* Motor Speed Slider */}
      <div className="rounded-xl border border-border bg-card/50 p-4">
        <MotorSlider
          label="Motor Speed"
          value={motorSpeed}
          onChange={handleMotorChange}
          disabled={disabled || activePreset !== null}
        />
      </div>

      {/* Motion Presets */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-foreground">Motion Presets</span>
          <span className="text-xs text-muted-foreground">
            {activePreset ? `Running preset ${activePreset}...` : "Select a preset"}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2">
          {KAIT_MOTION_PRESETS.map((preset) => (
            <motion.button
              key={preset.id}
              onClick={() => handlePreset(preset.id)}
              disabled={disabled || activePreset !== null}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={cn(
                "relative flex flex-col items-start rounded-lg border p-3 text-left transition-colors",
                activePreset === preset.id
                  ? "border-amber-500 bg-amber-500/10"
                  : "border-border bg-card/50 hover:border-border/80 hover:bg-muted/50",
                (disabled || activePreset !== null) && "cursor-not-allowed opacity-50"
              )}
            >
              <div className="flex items-center gap-2">
                {activePreset === preset.id ? (
                  <div className="h-2 w-2 animate-pulse rounded-full bg-amber-500" />
                ) : (
                  <Play className="h-3 w-3 text-muted-foreground" />
                )}
                <span className="text-sm font-medium text-foreground">
                  {preset.name}
                </span>
              </div>
              <span className="mt-1 text-xs text-muted-foreground">
                {preset.description}
              </span>
              <span className="mt-1 text-[10px] text-muted-foreground/70">
                ~{preset.duration / 1000}s
              </span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Emergency Stop */}
      <button
        onClick={handleStop}
        disabled={disabled}
        className={cn(
          "flex w-full items-center justify-center gap-2 rounded-lg bg-destructive px-4 py-3 text-sm font-semibold text-destructive-foreground transition-colors hover:bg-destructive/90",
          disabled && "cursor-not-allowed opacity-50"
        )}
      >
        <Square className="h-4 w-4" />
        Emergency Stop
      </button>
    </div>
  );
}
