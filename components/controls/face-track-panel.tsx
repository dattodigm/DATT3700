"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ScanFace, Square, Target, Settings2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { XYPad } from "./xy-pad";

interface FaceTrackPanelProps {
  deviceName: string;
  onServoChange: (servoId: number, panAngle: number, tiltAngle: number) => void;
  onTrackingToggle: (enabled: boolean) => void;
  onStop: () => void;
  facePosition?: { x: number; y: number } | null;
  isTracking?: boolean;
  disabled?: boolean;
}

export function FaceTrackPanel({
  deviceName,
  onServoChange,
  onTrackingToggle,
  onStop,
  facePosition = null,
  isTracking = false,
  disabled = false,
}: FaceTrackPanelProps) {
  const [servoPairs, setServoPairs] = useState([
    { id: 1, pan: 90, tilt: 90 },
    { id: 2, pan: 90, tilt: 90 },
    { id: 3, pan: 90, tilt: 90 },
    { id: 4, pan: 90, tilt: 90 },
  ]);
  const [selectedServo, setSelectedServo] = useState(1);
  const [trackingEnabled, setTrackingEnabled] = useState(isTracking);

  const handleServoChange = (servoId: number, pan: number, tilt: number) => {
    setServoPairs((prev) =>
      prev.map((s) => (s.id === servoId ? { ...s, pan, tilt } : s))
    );
    onServoChange(servoId, pan, tilt);
  };

  const handleXYChange = (x: number, y: number) => {
    // Map -255 to 255 range to 0 to 180 degrees
    const pan = Math.round(((x + 255) / 510) * 180);
    const tilt = Math.round(((y + 255) / 510) * 180);
    handleServoChange(selectedServo, pan, tilt);
  };

  const handleTrackingToggle = () => {
    const newState = !trackingEnabled;
    setTrackingEnabled(newState);
    onTrackingToggle(newState);
  };

  const currentServo = servoPairs.find((s) => s.id === selectedServo);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-pink-500/10">
            <ScanFace className="h-5 w-5 text-pink-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Face Tracking Control</h3>
            <p className="text-xs text-muted-foreground">4x Pan/Tilt Servo Pairs</p>
          </div>
        </div>

        {/* Tracking Toggle */}
        <button
          onClick={handleTrackingToggle}
          disabled={disabled}
          className={cn(
            "flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
            trackingEnabled
              ? "bg-pink-500 text-white glow-destructive"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          )}
        >
          <Target className={cn("h-3.5 w-3.5", trackingEnabled && "animate-pulse")} />
          {trackingEnabled ? "Tracking ON" : "Manual"}
        </button>
      </div>

      {/* Face Position Indicator */}
      {trackingEnabled && facePosition && (
        <div className="rounded-lg border border-pink-500/30 bg-pink-500/5 p-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Face Detected</span>
            <span className="font-mono text-pink-400">
              X: {facePosition.x.toFixed(0)} Y: {facePosition.y.toFixed(0)}
            </span>
          </div>
        </div>
      )}

      {/* Servo Selection */}
      <div className="space-y-3">
        <span className="text-sm font-medium text-foreground">Select Servo Pair</span>
        <div className="grid grid-cols-4 gap-2">
          {servoPairs.map((servo) => (
            <motion.button
              key={servo.id}
              onClick={() => setSelectedServo(servo.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={cn(
                "flex flex-col items-center rounded-lg border p-3 transition-colors",
                selectedServo === servo.id
                  ? "border-pink-500 bg-pink-500/10"
                  : "border-border bg-card/50 hover:border-border/80"
              )}
            >
              <span
                className={cn(
                  "text-sm font-medium",
                  selectedServo === servo.id ? "text-pink-400" : "text-foreground"
                )}
              >
                #{servo.id}
              </span>
              <span className="mt-1 text-[10px] text-muted-foreground">
                {servo.pan}/{servo.tilt}
              </span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* XY Control Pad */}
      <div className="rounded-xl border border-border bg-card/50 p-4">
        <div className="flex flex-col items-center">
          <XYPad
            label={`Servo #${selectedServo} Pan/Tilt`}
            x={currentServo ? (currentServo.pan - 90) * (255 / 90) : 0}
            y={currentServo ? (currentServo.tilt - 90) * (255 / 90) : 0}
            onChange={handleXYChange}
            xLabel="Pan"
            yLabel="Tilt"
            size={180}
            disabled={disabled || trackingEnabled}
          />
        </div>

        {/* Current Angles Display */}
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="rounded-lg bg-muted/50 p-2 text-center">
            <span className="block text-xs text-muted-foreground">Pan Angle</span>
            <span className="text-lg font-mono text-foreground">{currentServo?.pan || 90}</span>
          </div>
          <div className="rounded-lg bg-muted/50 p-2 text-center">
            <span className="block text-xs text-muted-foreground">Tilt Angle</span>
            <span className="text-lg font-mono text-foreground">{currentServo?.tilt || 90}</span>
          </div>
        </div>
      </div>

      {/* All Servos Overview */}
      <div className="rounded-xl border border-border bg-card/50 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Settings2 className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-foreground">All Servos Status</span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {servoPairs.map((servo) => (
            <div
              key={servo.id}
              className={cn(
                "flex items-center justify-between rounded-lg p-2",
                selectedServo === servo.id ? "bg-pink-500/10" : "bg-muted/30"
              )}
            >
              <span className="text-xs text-muted-foreground">Servo #{servo.id}</span>
              <span className="font-mono text-xs text-foreground">
                P:{servo.pan} T:{servo.tilt}
              </span>
            </div>
          ))}
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
