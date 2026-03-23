"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Flower2, Square, AlertTriangle, Leaf, Moon, Eye, Wind, Heart } from "lucide-react";
import { cn } from "@/lib/utils";
import { SUE_STATE_PRESETS } from "@/lib/types";

interface SuePanelProps {
  deviceName: string;
  onStateChange: (state: string) => void;
  onAngleChange: (angle: number) => void;
  onSpeedChange: (speed: number) => void;
  onLedChange: (r: number, g: number) => void;
  onStop: () => void;
  disabled?: boolean;
}

const stateIcons: Record<string, typeof AlertTriangle> = {
  danger: AlertTriangle,
  relax: Leaf,
  idle: Moon,
  alert: Eye,
  calm: Wind,
  breathe: Heart,
};

export function SuePanel({
  deviceName,
  onStateChange,
  onAngleChange,
  onSpeedChange,
  onLedChange,
  onStop,
  disabled = false,
}: SuePanelProps) {
  const [currentState, setCurrentState] = useState<string>("idle");
  const [servoAngle, setServoAngle] = useState(60); // Closed position
  const [stepSpeed, setStepSpeed] = useState(20);
  const [ledR, setLedR] = useState(0);
  const [ledG, setLedG] = useState(0);

  const handleStateSelect = (stateId: string) => {
    setCurrentState(stateId);
    onStateChange(stateId);
    // Update LED preview based on state preset
    const preset = SUE_STATE_PRESETS.find((p) => p.id === stateId);
    if (preset) {
      setLedR(preset.ledR);
      setLedG(preset.ledG);
    }
  };

  const handleAngleChange = (angle: number) => {
    setServoAngle(angle);
    onAngleChange(angle);
  };

  const handleSpeedChange = (speed: number) => {
    setStepSpeed(speed);
    onSpeedChange(speed);
  };

  const handleLedChange = (r: number, g: number) => {
    setLedR(r);
    setLedG(g);
    onLedChange(r, g);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10">
          <Flower2 className="h-5 w-5 text-emerald-400" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">Sue Servo Control</h3>
          <p className="text-xs text-muted-foreground">Single Servo + LED State Machine</p>
        </div>
      </div>

      {/* State Presets */}
      <div className="space-y-3">
        <span className="text-sm font-medium text-foreground">State Presets</span>
        <div className="grid grid-cols-3 gap-2">
          {SUE_STATE_PRESETS.map((preset) => {
            const Icon = stateIcons[preset.id] || Flower2;
            const isActive = currentState === preset.id;

            return (
              <motion.button
                key={preset.id}
                onClick={() => handleStateSelect(preset.id)}
                disabled={disabled}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  "flex flex-col items-center justify-center rounded-lg border p-3 transition-colors",
                  isActive
                    ? "border-emerald-500 bg-emerald-500/10"
                    : "border-border bg-card/50 hover:border-border/80 hover:bg-muted/50",
                  disabled && "cursor-not-allowed opacity-50"
                )}
              >
                <Icon
                  className={cn(
                    "h-5 w-5",
                    isActive ? "text-emerald-400" : "text-muted-foreground"
                  )}
                />
                <span
                  className={cn(
                    "mt-1.5 text-xs font-medium",
                    isActive ? "text-emerald-400" : "text-foreground"
                  )}
                >
                  {preset.name}
                </span>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Fine Control */}
      <div className="rounded-xl border border-border bg-card/50 p-4 space-y-4">
        <span className="text-sm font-medium text-foreground">Fine Control</span>

        {/* Servo Angle */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Servo Angle</span>
            <span className="font-mono text-xs text-muted-foreground">{servoAngle}deg</span>
          </div>
          <input
            type="range"
            min={0}
            max={180}
            value={servoAngle}
            onChange={(e) => handleAngleChange(parseInt(e.target.value))}
            disabled={disabled}
            className="w-full"
          />
          <div className="flex justify-between text-[10px] text-muted-foreground">
            <span>Closed (60)</span>
            <span>Open (120)</span>
          </div>
        </div>

        {/* Step Speed */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Step Speed</span>
            <span className="font-mono text-xs text-muted-foreground">{stepSpeed}ms/deg</span>
          </div>
          <input
            type="range"
            min={1}
            max={200}
            value={stepSpeed}
            onChange={(e) => handleSpeedChange(parseInt(e.target.value))}
            disabled={disabled}
            className="w-full"
          />
        </div>

        {/* LED Control */}
        <div className="space-y-2">
          <span className="text-xs text-muted-foreground">LED Control</span>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-red-400">Red LED</span>
                <span className="font-mono text-[10px] text-muted-foreground">{ledR}</span>
              </div>
              <input
                type="range"
                min={0}
                max={255}
                value={ledR}
                onChange={(e) => handleLedChange(parseInt(e.target.value), ledG)}
                disabled={disabled}
                className="w-full"
              />
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-green-400">Green LED</span>
                <span className="font-mono text-[10px] text-muted-foreground">{ledG}</span>
              </div>
              <input
                type="range"
                min={0}
                max={255}
                value={ledG}
                onChange={(e) => handleLedChange(ledR, parseInt(e.target.value))}
                disabled={disabled}
                className="w-full"
              />
            </div>
          </div>
          {/* LED Preview */}
          <div
            className="h-4 w-full rounded-full transition-colors"
            style={{
              background: `linear-gradient(90deg, rgb(${ledR}, ${ledG}, 0), rgb(${ledR}, ${ledG}, 0))`,
              boxShadow:
                ledR > 0 || ledG > 0
                  ? `0 0 20px rgba(${ledR}, ${ledG}, 0, 0.5)`
                  : "none",
            }}
          />
        </div>
      </div>

      {/* Emergency Stop */}
      <button
        onClick={onStop}
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
