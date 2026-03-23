"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Sparkles, Square, Palette } from "lucide-react";
import { cn } from "@/lib/utils";
import { MotorSlider } from "./motor-slider";
import { XYPad } from "./xy-pad";
import { SYLVIE_PRESETS } from "@/lib/types";

interface SylviePanelProps {
  deviceName: string;
  onMotor1Change: (dir: number, speed: number) => void;
  onMotor2Change: (dir: number, speed: number) => void;
  onLed1Change: (r: number, g: number, b: number) => void;
  onLed2Change: (r: number, g: number, b: number) => void;
  onPreset: (preset: number) => void;
  onAutoMode: (enabled: boolean) => void;
  onStop: () => void;
  disabled?: boolean;
}

export function SylviePanel({
  deviceName,
  onMotor1Change,
  onMotor2Change,
  onLed1Change,
  onLed2Change,
  onPreset,
  onAutoMode,
  onStop,
  disabled = false,
}: SylviePanelProps) {
  const [motor1Speed, setMotor1Speed] = useState(0);
  const [motor2Speed, setMotor2Speed] = useState(0);
  const [led1, setLed1] = useState({ r: 0, g: 0, b: 0 });
  const [led2, setLed2] = useState({ r: 0, g: 0, b: 0 });
  const [activePreset, setActivePreset] = useState<number>(3); // Default: Rest
  const [isAutoMode, setIsAutoMode] = useState(false);
  const [controlMode, setControlMode] = useState<"sliders" | "pad">("pad");

  const handleMotor1Change = useCallback(
    (speed: number) => {
      setMotor1Speed(speed);
      const dir = speed > 0 ? 1 : speed < 0 ? -1 : 0;
      onMotor1Change(dir, Math.abs(speed));
    },
    [onMotor1Change]
  );

  const handleMotor2Change = useCallback(
    (speed: number) => {
      setMotor2Speed(speed);
      const dir = speed > 0 ? 1 : speed < 0 ? -1 : 0;
      onMotor2Change(dir, Math.abs(speed));
    },
    [onMotor2Change]
  );

  // XY Pad controls both motors at once (differential drive)
  const handleXYChange = useCallback(
    (x: number, y: number) => {
      // Map XY to differential drive: Y = forward/back, X = turn
      const leftSpeed = Math.round(y + x * 0.5);
      const rightSpeed = Math.round(y - x * 0.5);
      handleMotor1Change(leftSpeed);
      handleMotor2Change(rightSpeed);
    },
    [handleMotor1Change, handleMotor2Change]
  );

  const handlePresetSelect = (preset: number) => {
    setActivePreset(preset);
    onPreset(preset);
  };

  const handleAutoModeToggle = () => {
    const newMode = !isAutoMode;
    setIsAutoMode(newMode);
    onAutoMode(newMode);
  };

  const handleStop = () => {
    setMotor1Speed(0);
    setMotor2Speed(0);
    setActivePreset(3);
    onStop();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-500/10">
            <Sparkles className="h-5 w-5 text-sky-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Sylvie Motor Control</h3>
            <p className="text-xs text-muted-foreground">2x DC Motors + RGB LED</p>
          </div>
        </div>

        {/* Auto Mode Toggle */}
        <button
          onClick={handleAutoModeToggle}
          disabled={disabled}
          className={cn(
            "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
            isAutoMode
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          )}
        >
          {isAutoMode ? "Auto ON" : "Manual"}
        </button>
      </div>

      {/* Control Mode Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setControlMode("pad")}
          className={cn(
            "flex-1 rounded-lg px-3 py-2 text-xs font-medium transition-colors",
            controlMode === "pad"
              ? "bg-primary/10 text-primary border border-primary/30"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          )}
        >
          2D Pad Control
        </button>
        <button
          onClick={() => setControlMode("sliders")}
          className={cn(
            "flex-1 rounded-lg px-3 py-2 text-xs font-medium transition-colors",
            controlMode === "sliders"
              ? "bg-primary/10 text-primary border border-primary/30"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          )}
        >
          Individual Sliders
        </button>
      </div>

      {/* Motor Control Area */}
      <div className="rounded-xl border border-border bg-card/50 p-4">
        {controlMode === "pad" ? (
          <div className="flex flex-col items-center">
            <XYPad
              label="Drive Control"
              x={(motor1Speed + motor2Speed) / 2}
              y={(motor1Speed - motor2Speed) / 2}
              onChange={handleXYChange}
              xLabel="Turn"
              yLabel="Speed"
              size={180}
              disabled={disabled || isAutoMode}
            />
          </div>
        ) : (
          <div className="space-y-4">
            <MotorSlider
              label="Motor 1 (Left)"
              value={motor1Speed}
              onChange={handleMotor1Change}
              disabled={disabled || isAutoMode}
            />
            <MotorSlider
              label="Motor 2 (Right)"
              value={motor2Speed}
              onChange={handleMotor2Change}
              disabled={disabled || isAutoMode}
            />
          </div>
        )}
      </div>

      {/* Presets */}
      <div className="space-y-3">
        <span className="text-sm font-medium text-foreground">Presets</span>
        <div className="grid grid-cols-2 gap-2">
          {SYLVIE_PRESETS.map((preset) => (
            <motion.button
              key={preset.id}
              onClick={() => handlePresetSelect(preset.id)}
              disabled={disabled}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={cn(
                "flex flex-col items-start rounded-lg border p-3 text-left transition-colors",
                activePreset === preset.id
                  ? "border-sky-500 bg-sky-500/10"
                  : "border-border bg-card/50 hover:border-border/80 hover:bg-muted/50",
                disabled && "cursor-not-allowed opacity-50"
              )}
            >
              <span className="text-sm font-medium text-foreground">{preset.name}</span>
              <span className="mt-0.5 text-xs text-muted-foreground">
                {preset.description}
              </span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* LED Color Picker */}
      <div className="rounded-xl border border-border bg-card/50 p-4 space-y-4">
        <div className="flex items-center gap-2">
          <Palette className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-foreground">LED Control</span>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* LED 1 */}
          <div className="space-y-2">
            <span className="text-xs text-muted-foreground">LED 1</span>
            <div className="space-y-1">
              <input
                type="range"
                min={0}
                max={255}
                value={led1.r}
                onChange={(e) => {
                  const r = parseInt(e.target.value);
                  setLed1({ ...led1, r });
                  onLed1Change(r, led1.g, led1.b);
                }}
                className="w-full"
                disabled={disabled || isAutoMode}
              />
              <input
                type="range"
                min={0}
                max={255}
                value={led1.g}
                onChange={(e) => {
                  const g = parseInt(e.target.value);
                  setLed1({ ...led1, g });
                  onLed1Change(led1.r, g, led1.b);
                }}
                className="w-full"
                disabled={disabled || isAutoMode}
              />
              <input
                type="range"
                min={0}
                max={255}
                value={led1.b}
                onChange={(e) => {
                  const b = parseInt(e.target.value);
                  setLed1({ ...led1, b });
                  onLed1Change(led1.r, led1.g, b);
                }}
                className="w-full"
                disabled={disabled || isAutoMode}
              />
            </div>
            <div
              className="h-6 w-full rounded-lg"
              style={{
                backgroundColor: `rgb(${led1.r}, ${led1.g}, ${led1.b})`,
                boxShadow: `0 0 15px rgba(${led1.r}, ${led1.g}, ${led1.b}, 0.5)`,
              }}
            />
          </div>

          {/* LED 2 */}
          <div className="space-y-2">
            <span className="text-xs text-muted-foreground">LED 2</span>
            <div className="space-y-1">
              <input
                type="range"
                min={0}
                max={255}
                value={led2.r}
                onChange={(e) => {
                  const r = parseInt(e.target.value);
                  setLed2({ ...led2, r });
                  onLed2Change(r, led2.g, led2.b);
                }}
                className="w-full"
                disabled={disabled || isAutoMode}
              />
              <input
                type="range"
                min={0}
                max={255}
                value={led2.g}
                onChange={(e) => {
                  const g = parseInt(e.target.value);
                  setLed2({ ...led2, g });
                  onLed2Change(led2.r, g, led2.b);
                }}
                className="w-full"
                disabled={disabled || isAutoMode}
              />
              <input
                type="range"
                min={0}
                max={255}
                value={led2.b}
                onChange={(e) => {
                  const b = parseInt(e.target.value);
                  setLed2({ ...led2, b });
                  onLed2Change(led2.r, led2.g, b);
                }}
                className="w-full"
                disabled={disabled || isAutoMode}
              />
            </div>
            <div
              className="h-6 w-full rounded-lg"
              style={{
                backgroundColor: `rgb(${led2.r}, ${led2.g}, ${led2.b})`,
                boxShadow: `0 0 15px rgba(${led2.r}, ${led2.g}, ${led2.b}, 0.5)`,
              }}
            />
          </div>
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
