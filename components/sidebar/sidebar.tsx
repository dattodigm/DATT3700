"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Flower2,
  Layers,
  History,
  Settings,
  Wifi,
  WifiOff,
  Zap,
  Sparkles,
  ScanFace,
  HelpCircle,
  Plus,
  RefreshCw,
  CheckCircle2,
  Circle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";
import type { Device, NodeType } from "@/lib/types";
import { NODE_TYPE_INFO } from "@/lib/utils";
import { NodeList } from "./node-list";
import { AddDeviceDialog } from "./add-device-dialog";

const nodeIcons: Record<string, typeof Zap> = {
  kait: Zap,
  sue: Flower2,
  sylvie: Sparkles,
  face_track: ScanFace,
  unknown: HelpCircle,
};

interface SidebarProps {
  devices: Device[];
  onScan: (mode: "auto" | "mdns" | "gateway") => Promise<void>;
  onAddDevice: (device: { name: string; ip: string; port: number; node_type: NodeType }) => Promise<void>;
  onSelectDevice: (name: string) => Promise<void>;
  onToggleEmotionTarget: (name: string, enabled: boolean) => Promise<void>;
  isScanning?: boolean;
}

export function Sidebar({
  devices,
  onScan,
  onAddDevice,
  onSelectDevice,
  onToggleEmotionTarget,
  isScanning = false,
}: SidebarProps) {
  const {
    sidebarOpen,
    toggleSidebar,
    activePanel,
    setActivePanel,
    selectedDevice,
    emotionTargets,
  } = useAppStore();

  const [showAddDialog, setShowAddDialog] = useState(false);

  const navItems = [
    { id: "nodes" as const, icon: Layers, label: "Nodes" },
    { id: "sequences" as const, icon: History, label: "Sequences" },
    { id: "settings" as const, icon: Settings, label: "Settings" },
  ];

  return (
    <>
      <motion.aside
        initial={false}
        animate={{ width: sidebarOpen ? 320 : 64 }}
        transition={{ duration: 0.2, ease: "easeInOut" }}
        className="flex h-screen flex-col border-r border-border bg-card"
      >
        {/* Header */}
        <div className="flex h-16 items-center justify-between border-b border-border px-4">
          <AnimatePresence mode="wait">
            {sidebarOpen && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="flex items-center gap-3"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                  <Flower2 className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h1 className="text-sm font-semibold text-foreground">F7OWER</h1>
                  <p className="text-xs text-muted-foreground">Control Panel</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <button
            onClick={toggleSidebar}
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            {sidebarOpen ? (
              <ChevronLeft className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-1 p-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActivePanel(item.id)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                activePanel === item.id
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              <AnimatePresence mode="wait">
                {sidebarOpen && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: "auto" }}
                    exit={{ opacity: 0, width: 0 }}
                    className="overflow-hidden whitespace-nowrap"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
            </button>
          ))}
        </nav>

        {/* Panel Content */}
        <AnimatePresence mode="wait">
          {sidebarOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-1 flex-col overflow-hidden"
            >
              {activePanel === "nodes" && (
                <div className="flex flex-1 flex-col overflow-hidden">
                  {/* Scan Controls */}
                  <div className="border-b border-border p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs font-medium text-muted-foreground">
                        Device Discovery
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {devices.length} found
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => onScan("auto")}
                        disabled={isScanning}
                        className={cn(
                          "flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90",
                          isScanning && "opacity-50 cursor-not-allowed"
                        )}
                      >
                        <RefreshCw className={cn("h-3.5 w-3.5", isScanning && "animate-spin")} />
                        {isScanning ? "Scanning..." : "Scan Network"}
                      </button>
                      <button
                        onClick={() => setShowAddDialog(true)}
                        className="flex items-center justify-center rounded-lg bg-secondary px-3 py-2 text-xs font-medium text-secondary-foreground transition-colors hover:bg-secondary/80"
                      >
                        <Plus className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Node List */}
                  <NodeList
                    devices={devices}
                    selectedDevice={selectedDevice}
                    emotionTargets={emotionTargets}
                    onSelectDevice={onSelectDevice}
                    onToggleEmotionTarget={onToggleEmotionTarget}
                  />

                  {/* Mode Status */}
                  <div className="border-t border-border p-3">
                    <div className="mb-2 text-xs font-medium text-muted-foreground">
                      Emotion Routing
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {Array.from(emotionTargets).length === 0 ? (
                        <span className="text-xs text-muted-foreground">
                          No targets selected
                        </span>
                      ) : (
                        Array.from(emotionTargets).map((name) => (
                          <span
                            key={name}
                            className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
                          >
                            <CheckCircle2 className="h-3 w-3" />
                            {name}
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              )}

              {activePanel === "sequences" && (
                <div className="flex flex-1 flex-col p-3">
                  <div className="mb-3 text-xs font-medium text-muted-foreground">
                    Recorded Sequences
                  </div>
                  <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed border-border">
                    <p className="text-center text-xs text-muted-foreground">
                      No sequences recorded yet.
                      <br />
                      Use the recorder panel to create sequences.
                    </p>
                  </div>
                </div>
              )}

              {activePanel === "settings" && (
                <div className="flex flex-1 flex-col p-3">
                  <div className="mb-3 text-xs font-medium text-muted-foreground">
                    Connection Settings
                  </div>
                  <div className="space-y-3 text-xs">
                    <div className="flex items-center justify-between rounded-lg bg-muted p-3">
                      <span className="text-muted-foreground">Backend URL</span>
                      <span className="font-mono text-foreground">localhost:5000</span>
                    </div>
                    <div className="flex items-center justify-between rounded-lg bg-muted p-3">
                      <span className="text-muted-foreground">OSC Port</span>
                      <span className="font-mono text-foreground">8888</span>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Connection Status Footer */}
        <div className="border-t border-border p-3">
          <div className="flex items-center gap-2">
            <div className={cn("status-dot", devices.length > 0 ? "status-online" : "status-offline")} />
            <AnimatePresence mode="wait">
              {sidebarOpen && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-xs text-muted-foreground"
                >
                  {devices.length > 0 ? `${devices.length} device${devices.length > 1 ? "s" : ""} online` : "No devices"}
                </motion.span>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.aside>

      {/* Add Device Dialog */}
      <AddDeviceDialog
        open={showAddDialog}
        onClose={() => setShowAddDialog(false)}
        onAdd={onAddDevice}
      />
    </>
  );
}
