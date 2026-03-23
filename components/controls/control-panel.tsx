"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Layers, Zap, Flower2, Sparkles, ScanFace, HelpCircle, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Device, NodeType } from "@/lib/types";
import { KaitPanel } from "./kait-panel";
import { SuePanel } from "./sue-panel";
import { SylviePanel } from "./sylvie-panel";
import { FaceTrackPanel } from "./face-track-panel";
import { RawOscPanel } from "./raw-osc-panel";

const nodeIcons: Record<string, typeof Zap> = {
  kait: Zap,
  sue: Flower2,
  sylvie: Sparkles,
  face_track: ScanFace,
  unknown: HelpCircle,
};

interface ControlPanelProps {
  device: Device | null;
  forcedNodeType: NodeType | null;
  facePosition?: { x: number; y: number } | null;
  isTracking?: boolean;
  onOSCSend: (address: string, args: (number | string)[]) => void;
  disabled?: boolean;
}

export function ControlPanel({
  device,
  forcedNodeType,
  facePosition,
  isTracking,
  onOSCSend,
  disabled = false,
}: ControlPanelProps) {
  const nodeType = forcedNodeType || device?.node_type || "unknown";
  const deviceName = device?.name || "No Device";
  const Icon = nodeIcons[nodeType] || HelpCircle;

  // OSC command helpers
  const sendMotor = (motor: number, dir: number, speed: number = 255) => {
    if (nodeType === "kait") {
      // Kait uses combined speed value (-255 to 255)
      onOSCSend("/motor", [dir * speed]);
    } else {
      // Sylvie uses separate dir and speed
      onOSCSend(`/motor${motor}`, [dir, speed]);
    }
  };

  const sendMotion = (mode: number) => {
    onOSCSend("/motion", [mode]);
  };

  const sendPreset = (preset: number) => {
    onOSCSend("/preset", [preset]);
  };

  const sendState = (state: string) => {
    onOSCSend("/state", [state]);
  };

  const sendAngle = (angle: number) => {
    onOSCSend("/angle", [angle]);
  };

  const sendSpeed = (speed: number) => {
    onOSCSend("/speed", [speed]);
  };

  const sendLed = (led: number, r: number, g: number, b?: number) => {
    if (b !== undefined) {
      onOSCSend(`/led${led}`, [r, g, b]);
    } else {
      onOSCSend("/led", [r, g]);
    }
  };

  const sendServo = (servoId: number, pan: number, tilt: number) => {
    onOSCSend(`/servo/${servoId}`, [pan, tilt]);
  };

  const sendTrackingMode = (enabled: boolean) => {
    onOSCSend("/track/auto", [enabled ? 1 : 0]);
  };

  const sendAutoMode = (enabled: boolean) => {
    onOSCSend("/auto", [enabled ? 1 : 0]);
  };

  const sendStop = () => {
    onOSCSend("/stop", []);
  };

  if (!device) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="mb-4 flex h-16 w-16 mx-auto items-center justify-center rounded-full bg-muted">
            <Layers className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold text-foreground">No Device Selected</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Select a device from the sidebar to start controlling
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <AnimatePresence mode="wait">
        <motion.div
          key={`${deviceName}-${nodeType}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.15 }}
          className="p-6"
        >
          {/* Node Type Tabs */}
          <div className="mb-6 flex items-center gap-2 overflow-x-auto pb-2">
            {Object.entries(nodeIcons).map(([type, TypeIcon]) => (
              <button
                key={type}
                onClick={() => {
                  // This would update the forced node type in the parent
                }}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium whitespace-nowrap transition-colors",
                  nodeType === type
                    ? "bg-primary/10 text-primary border border-primary/30"
                    : "bg-secondary text-muted-foreground hover:text-foreground hover:bg-secondary/80"
                )}
              >
                <TypeIcon className="h-3.5 w-3.5" />
                {type === "face_track" ? "Face Track" : type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>

          {/* Control Panel based on Node Type */}
          {nodeType === "kait" && (
            <KaitPanel
              deviceName={deviceName}
              onMotorChange={(speed) => sendMotor(1, speed > 0 ? 1 : speed < 0 ? -1 : 0, Math.abs(speed))}
              onMotionPreset={sendMotion}
              onStop={sendStop}
              disabled={disabled}
            />
          )}

          {nodeType === "sue" && (
            <SuePanel
              deviceName={deviceName}
              onStateChange={sendState}
              onAngleChange={sendAngle}
              onSpeedChange={sendSpeed}
              onLedChange={(r, g) => sendLed(1, r, g)}
              onStop={sendStop}
              disabled={disabled}
            />
          )}

          {nodeType === "sylvie" && (
            <SylviePanel
              deviceName={deviceName}
              onMotor1Change={(dir, speed) => sendMotor(1, dir, speed)}
              onMotor2Change={(dir, speed) => sendMotor(2, dir, speed)}
              onLed1Change={(r, g, b) => sendLed(1, r, g, b)}
              onLed2Change={(r, g, b) => sendLed(2, r, g, b)}
              onPreset={sendPreset}
              onAutoMode={sendAutoMode}
              onStop={sendStop}
              disabled={disabled}
            />
          )}

          {nodeType === "face_track" && (
            <FaceTrackPanel
              deviceName={deviceName}
              onServoChange={sendServo}
              onTrackingToggle={sendTrackingMode}
              onStop={sendStop}
              facePosition={facePosition}
              isTracking={isTracking}
              disabled={disabled}
            />
          )}

          {nodeType === "unknown" && (
            <RawOscPanel
              deviceName={deviceName}
              onSend={onOSCSend}
              disabled={disabled}
            />
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
