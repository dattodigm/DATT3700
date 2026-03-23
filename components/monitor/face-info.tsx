"use client";

import { motion } from "framer-motion";
import { User, Target, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import type { FaceData } from "@/lib/types";

interface FaceInfoProps {
  primary: FaceData | null;
  faces: FaceData[];
  cameraRunning: boolean;
}

export function FaceInfo({ primary, faces, cameraRunning }: FaceInfoProps) {
  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium text-foreground">Face Detection</span>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={cn(
                "status-dot",
                faces.length > 0 ? "status-active" : "status-offline"
              )}
            />
            <span className="text-xs text-muted-foreground">
              {faces.length} face{faces.length !== 1 ? "s" : ""}
            </span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {!cameraRunning ? (
          <div className="flex flex-col items-center justify-center py-4">
            <User className="h-8 w-8 text-muted-foreground/30" />
            <p className="mt-2 text-sm text-muted-foreground">Camera is off</p>
          </div>
        ) : faces.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-4">
            <Target className="h-8 w-8 text-muted-foreground/30" />
            <p className="mt-2 text-sm text-muted-foreground">No faces detected</p>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Primary Face */}
            {primary && (
              <div className="rounded-lg border border-primary/30 bg-primary/5 p-3">
                <div className="mb-2 flex items-center gap-2">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20">
                    <Target className="h-3.5 w-3.5 text-primary" />
                  </div>
                  <span className="text-sm font-medium text-primary">Primary Target</span>
                </div>

                <div className="grid grid-cols-2 gap-3 font-mono text-xs">
                  <div className="rounded-md bg-muted/50 p-2">
                    <span className="text-muted-foreground">Position</span>
                    <p className="text-foreground">
                      X: {primary.x.toFixed(0)}, Y: {primary.y.toFixed(0)}
                    </p>
                  </div>
                  <div className="rounded-md bg-muted/50 p-2">
                    <span className="text-muted-foreground">Size</span>
                    <p className="text-foreground">
                      {primary.w.toFixed(0)} x {primary.h.toFixed(0)}
                    </p>
                  </div>
                </div>

                {/* Confidence */}
                <div className="mt-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Confidence</span>
                    <span className="text-primary">
                      {(primary.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="mt-1 h-1.5 w-full rounded-full bg-muted overflow-hidden">
                    <motion.div
                      className="h-1.5 rounded-full bg-primary"
                      initial={{ width: 0 }}
                      animate={{ width: `${primary.confidence * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Other Faces */}
            {faces.length > 1 && (
              <div className="space-y-2">
                <span className="text-xs text-muted-foreground">
                  Other Faces ({faces.length - 1})
                </span>
                <div className="grid gap-2">
                  {faces.slice(1, 4).map((face, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between rounded-md bg-muted/30 px-3 py-2 text-xs"
                    >
                      <span className="text-muted-foreground">Face #{idx + 2}</span>
                      <span className="font-mono text-foreground">
                        {face.x.toFixed(0)}, {face.y.toFixed(0)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
