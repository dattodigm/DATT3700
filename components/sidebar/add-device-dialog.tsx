"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import type { NodeType } from "@/lib/types";

interface AddDeviceDialogProps {
  open: boolean;
  onClose: () => void;
  onAdd: (device: {
    name: string;
    ip: string;
    port: number;
    node_type: NodeType;
  }) => Promise<void>;
}

const nodeTypeOptions: { value: NodeType; label: string }[] = [
  { value: "kait", label: "Kait (DC Motor)" },
  { value: "sue", label: "Sue (Servo)" },
  { value: "sylvie", label: "Sylvie (2x Motor + LED)" },
  { value: "face_track", label: "Face Track (Multi-Servo)" },
  { value: "unknown", label: "Unknown (Raw OSC)" },
];

export function AddDeviceDialog({ open, onClose, onAdd }: AddDeviceDialogProps) {
  const [name, setName] = useState("");
  const [ip, setIp] = useState("");
  const [port, setPort] = useState("8888");
  const [nodeType, setNodeType] = useState<NodeType>("unknown");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ip.trim()) return;

    setIsSubmitting(true);
    try {
      await onAdd({
        name: name.trim() || `device_${ip.replace(/\./g, "_")}`,
        ip: ip.trim(),
        port: parseInt(port) || 8888,
        node_type: nodeType,
      });
      // Reset form
      setName("");
      setIp("");
      setPort("8888");
      setNodeType("unknown");
      onClose();
    } catch (error) {
      console.error("Failed to add device:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.15 }}
            className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border border-border bg-card p-6 shadow-xl"
          >
            {/* Header */}
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-foreground">Add Device</h2>
              <button
                onClick={onClose}
                className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm text-muted-foreground">
                  Device Name (optional)
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., flower_1"
                  className="w-full rounded-lg border border-border bg-input px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-muted-foreground">
                  IP Address *
                </label>
                <input
                  type="text"
                  value={ip}
                  onChange={(e) => setIp(e.target.value)}
                  placeholder="e.g., 192.168.1.100"
                  required
                  className="w-full rounded-lg border border-border bg-input px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-muted-foreground">
                  OSC Port
                </label>
                <input
                  type="number"
                  value={port}
                  onChange={(e) => setPort(e.target.value)}
                  placeholder="8888"
                  className="w-full rounded-lg border border-border bg-input px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-muted-foreground">
                  Node Type
                </label>
                <select
                  value={nodeType}
                  onChange={(e) => setNodeType(e.target.value as NodeType)}
                  className="w-full rounded-lg border border-border bg-input px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {nodeTypeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 rounded-lg border border-border bg-secondary px-4 py-2.5 text-sm font-medium text-secondary-foreground transition-colors hover:bg-secondary/80"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!ip.trim() || isSubmitting}
                  className={cn(
                    "flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
                    (!ip.trim() || isSubmitting) && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <Plus className="h-4 w-4" />
                  {isSubmitting ? "Adding..." : "Add Device"}
                </button>
              </div>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
