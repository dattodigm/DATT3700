"use client";

import { useState, useRef } from "react";
import { motion } from "framer-motion";
import {
  Camera,
  CameraOff,
  Play,
  Square,
  RefreshCw,
  ChevronDown,
  Maximize2,
  Minimize2,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface CameraMonitorProps {
  cameras: number[];
  currentCamera: number;
  isRunning: boolean;
  onStart: (cameraIndex: number) => void;
  onStop: () => void;
  onSwitch: (cameraIndex: number) => void;
  onRefreshCameras: () => void;
  videoFeedUrl?: string;
}

export function CameraMonitor({
  cameras,
  currentCamera,
  isRunning,
  onStart,
  onStop,
  onSwitch,
  onRefreshCameras,
  videoFeedUrl = "/video_feed",
}: CameraMonitorProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showCameraSelect, setShowCameraSelect] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  // Force refresh video feed when running state changes
  const feedSrc = isRunning ? `${videoFeedUrl}?ts=${Date.now()}` : "";

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          {isRunning ? (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse-recording" />
              <span className="text-sm font-medium text-foreground">LIVE</span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <CameraOff className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium text-muted-foreground">OFF</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Camera Selector */}
          <div className="relative">
            <button
              onClick={() => setShowCameraSelect(!showCameraSelect)}
              className="flex items-center gap-1 rounded-lg bg-secondary px-2 py-1.5 text-xs font-medium text-secondary-foreground transition-colors hover:bg-secondary/80"
            >
              <Camera className="h-3.5 w-3.5" />
              Camera {currentCamera}
              <ChevronDown className="h-3 w-3" />
            </button>

            {showCameraSelect && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowCameraSelect(false)}
                />
                <div className="absolute right-0 top-full z-20 mt-1 w-40 rounded-lg border border-border bg-card p-1 shadow-xl">
                  {cameras.map((cam) => (
                    <button
                      key={cam}
                      onClick={() => {
                        if (isRunning) {
                          onSwitch(cam);
                        } else {
                          onStart(cam);
                        }
                        setShowCameraSelect(false);
                      }}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-md px-3 py-2 text-xs transition-colors",
                        currentCamera === cam
                          ? "bg-primary/10 text-primary"
                          : "text-foreground hover:bg-muted"
                      )}
                    >
                      <Camera className="h-3.5 w-3.5" />
                      Camera {cam}
                    </button>
                  ))}
                  <div className="my-1 border-t border-border" />
                  <button
                    onClick={() => {
                      onRefreshCameras();
                      setShowCameraSelect(false);
                    }}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                    Refresh List
                  </button>
                </div>
              </>
            )}
          </div>

          {/* Expand/Collapse */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            {isExpanded ? (
              <Minimize2 className="h-4 w-4" />
            ) : (
              <Maximize2 className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Video Feed */}
      <div
        className={cn(
          "relative bg-background transition-all",
          isExpanded ? "aspect-video" : "aspect-video max-h-64"
        )}
      >
        {isRunning ? (
          <img
            ref={imgRef}
            src={feedSrc}
            alt="Live camera feed"
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center">
            <CameraOff className="h-12 w-12 text-muted-foreground/30" />
            <p className="mt-3 text-sm text-muted-foreground">Camera is off</p>
          </div>
        )}

        {/* Face Detection Overlay would go here */}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 border-t border-border p-3">
        {isRunning ? (
          <button
            onClick={onStop}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground transition-colors hover:bg-destructive/90"
          >
            <Square className="h-4 w-4" />
            Stop Camera
          </button>
        ) : (
          <button
            onClick={() => onStart(currentCamera)}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            <Play className="h-4 w-4" />
            Start Camera
          </button>
        )}
      </div>
    </div>
  );
}
