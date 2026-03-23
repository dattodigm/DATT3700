"use client";

import { motion } from "framer-motion";
import {
  Zap,
  Flower2,
  Sparkles,
  ScanFace,
  HelpCircle,
  Check,
  Radio,
} from "lucide-react";
import { cn, NODE_TYPE_INFO } from "@/lib/utils";
import type { Device, NodeType } from "@/lib/types";

const nodeIcons: Record<string, typeof Zap> = {
  kait: Zap,
  sue: Flower2,
  sylvie: Sparkles,
  face_track: ScanFace,
  unknown: HelpCircle,
};

interface NodeListProps {
  devices: Device[];
  selectedDevice: string | null;
  emotionTargets: Set<string>;
  onSelectDevice: (name: string) => Promise<void>;
  onToggleEmotionTarget: (name: string, enabled: boolean) => Promise<void>;
}

export function NodeList({
  devices,
  selectedDevice,
  emotionTargets,
  onSelectDevice,
  onToggleEmotionTarget,
}: NodeListProps) {
  // Group devices by node type
  const groupedDevices = devices.reduce(
    (acc, device) => {
      const type = device.node_type || "unknown";
      if (!acc[type]) acc[type] = [];
      acc[type].push(device);
      return acc;
    },
    {} as Record<string, Device[]>
  );

  const nodeTypes = Object.keys(groupedDevices).sort((a, b) => {
    const order = ["kait", "sue", "sylvie", "face_track", "unknown"];
    return order.indexOf(a) - order.indexOf(b);
  });

  if (devices.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center p-6 text-center">
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          <Radio className="h-6 w-6 text-muted-foreground" />
        </div>
        <p className="text-sm text-muted-foreground">No devices found</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Click &quot;Scan Network&quot; to discover ESP32 nodes
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-2">
      {nodeTypes.map((type) => {
        const info = NODE_TYPE_INFO[type] || NODE_TYPE_INFO.unknown;
        const Icon = nodeIcons[type] || HelpCircle;
        const typeDevices = groupedDevices[type];

        return (
          <div key={type} className="mb-4">
            <div className="mb-2 flex items-center gap-2 px-2">
              <Icon className={cn("h-3.5 w-3.5", info.color)} />
              <span className="text-xs font-medium text-muted-foreground">
                {info.label} ({typeDevices.length})
              </span>
            </div>

            <div className="space-y-1">
              {typeDevices.map((device) => {
                const isSelected = selectedDevice === device.name;
                const isEmotionTarget = emotionTargets.has(device.name);

                return (
                  <motion.div
                    key={device.name}
                    layout
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={cn(
                      "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors cursor-pointer",
                      isSelected
                        ? "bg-primary/10 border border-primary/30"
                        : "hover:bg-muted border border-transparent"
                    )}
                    onClick={() => onSelectDevice(device.name)}
                  >
                    {/* Selection indicator */}
                    <div
                      className={cn(
                        "flex h-5 w-5 items-center justify-center rounded-full border transition-colors",
                        isSelected
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-muted-foreground/30"
                      )}
                    >
                      {isSelected && <Check className="h-3 w-3" />}
                    </div>

                    {/* Device info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="truncate text-sm font-medium text-foreground">
                          {device.label || device.name}
                        </span>
                        <div className="status-dot status-online" />
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="font-mono">{device.ip}</span>
                        <span>:{device.port}</span>
                      </div>
                    </div>

                    {/* Emotion target toggle */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleEmotionTarget(device.name, !isEmotionTarget);
                      }}
                      className={cn(
                        "flex h-6 w-6 items-center justify-center rounded-md transition-colors",
                        isEmotionTarget
                          ? "bg-primary/20 text-primary"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground"
                      )}
                      title={
                        isEmotionTarget
                          ? "Remove from emotion routing"
                          : "Add to emotion routing"
                      }
                    >
                      <Radio className="h-3.5 w-3.5" />
                    </button>
                  </motion.div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
