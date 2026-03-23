"use client";

import { useEffect, useState, useCallback } from "react";
import useSWR from "swr";
import { Sidebar } from "@/components/sidebar";
import { ControlPanel } from "@/components/controls";
import { CameraMonitor, EmotionMonitor, FaceInfo } from "@/components/monitor";
import { SequenceRecorder } from "@/components/recorder";
import { useAppStore } from "@/lib/store";
import { fetchJSON, postJSON } from "@/lib/utils";
import type { Device, NodeType, FaceAPIResponse, MotionSequence } from "@/lib/types";

// API fetchers
const fetcher = <T,>(url: string) => fetchJSON<T>(url);

export default function HomePage() {
  const {
    devices,
    setDevices,
    selectedDevice,
    selectDevice,
    emotionTargets,
    setEmotionTargets,
    toggleEmotionTarget,
    sidebarOpen,
    forcedNodeType,
    isRecording,
    addRecordedEvent,
  } = useAppStore();

  const [isScanning, setIsScanning] = useState(false);
  const [cameras, setCameras] = useState<number[]>([0]);
  const [currentCamera, setCurrentCamera] = useState(0);
  const [isCameraRunning, setIsCameraRunning] = useState(false);

  // Fetch devices
  const { data: devicesData, mutate: mutateDevices } = useSWR<{
    devices: Device[];
    selected: string | null;
    emotion_targets: string[];
  }>("/api/devices", fetcher, {
    refreshInterval: 5000,
    onSuccess: (data) => {
      setDevices(data.devices);
      if (data.selected && !selectedDevice) {
        selectDevice(data.selected);
      }
      setEmotionTargets(data.emotion_targets);
    },
  });

  // Fetch face data (when camera is running)
  const { data: faceData } = useSWR<FaceAPIResponse>(
    isCameraRunning ? "/api/faces" : null,
    fetcher,
    { refreshInterval: 100 }
  );

  // Fetch camera state
  const { data: cameraState, mutate: mutateCameraState } = useSWR<{
    running: boolean;
    index: number;
  }>("/api/camera/state", fetcher, {
    refreshInterval: 2000,
    onSuccess: (data) => {
      setIsCameraRunning(data.running);
      setCurrentCamera(data.index);
    },
  });

  // Fetch available cameras
  const refreshCameras = useCallback(async () => {
    try {
      const data = await fetchJSON<{ cameras: number[] }>("/api/cameras");
      setCameras(data.cameras);
    } catch (error) {
      console.error("Failed to fetch cameras:", error);
    }
  }, []);

  useEffect(() => {
    refreshCameras();
  }, [refreshCameras]);

  // Device management handlers
  const handleScan = async (mode: "auto" | "mdns" | "gateway") => {
    setIsScanning(true);
    try {
      await postJSON("/api/devices/scan", { mode });
      await mutateDevices();
    } catch (error) {
      console.error("Scan failed:", error);
    } finally {
      setIsScanning(false);
    }
  };

  const handleAddDevice = async (device: {
    name: string;
    ip: string;
    port: number;
    node_type: NodeType;
  }) => {
    await postJSON("/api/osc/target", device);
    await mutateDevices();
  };

  const handleSelectDevice = async (name: string) => {
    await postJSON("/api/devices/select", { name });
    selectDevice(name);
  };

  const handleToggleEmotionTarget = async (name: string, enabled: boolean) => {
    const currentTargets = Array.from(emotionTargets);
    const newTargets = enabled
      ? [...currentTargets, name]
      : currentTargets.filter((t) => t !== name);

    await postJSON("/api/devices/emotion_targets", { names: newTargets });
    toggleEmotionTarget(name);
  };

  // Camera handlers
  const handleStartCamera = async (index: number) => {
    try {
      await postJSON("/api/camera/start", { index });
      setIsCameraRunning(true);
      setCurrentCamera(index);
      await mutateCameraState();
    } catch (error) {
      console.error("Failed to start camera:", error);
    }
  };

  const handleStopCamera = async () => {
    try {
      await postJSON("/api/camera/stop", {});
      setIsCameraRunning(false);
      await mutateCameraState();
    } catch (error) {
      console.error("Failed to stop camera:", error);
    }
  };

  const handleSwitchCamera = async (index: number) => {
    try {
      await postJSON("/api/camera/switch", { index });
      setCurrentCamera(index);
      await mutateCameraState();
    } catch (error) {
      console.error("Failed to switch camera:", error);
    }
  };

  // OSC command handler
  const handleOSCSend = useCallback(
    async (address: string, args: (number | string)[]) => {
      try {
        await postJSON("/api/osc/raw", {
          address,
          args,
          target: selectedDevice,
          source: "manual",
        });

        // Record event if recording
        if (isRecording) {
          addRecordedEvent({
            type: address.includes("motor")
              ? "motor"
              : address.includes("led")
                ? "led"
                : address.includes("servo") || address.includes("angle")
                  ? "servo"
                  : address.includes("preset")
                    ? "preset"
                    : "motion",
            target: selectedDevice || undefined,
            address,
            args,
          });
        }
      } catch (error) {
        console.error("OSC send failed:", error);
      }
    },
    [selectedDevice, isRecording, addRecordedEvent]
  );

  // Sequence handlers
  const handleSaveSequence = async (sequence: MotionSequence) => {
    await postJSON("/api/sequence/save", sequence);
  };

  const handleLoadSequence = async (name: string): Promise<MotionSequence | null> => {
    try {
      const data = await fetchJSON<{ sequence: MotionSequence }>(
        `/api/sequence/load?name=${encodeURIComponent(name)}`
      );
      return data.sequence;
    } catch {
      return null;
    }
  };

  const handlePlaySequence = (sequence: MotionSequence) => {
    // Play sequence events
    sequence.events.forEach((event) => {
      setTimeout(() => {
        handleOSCSend(event.address, event.args);
      }, event.timestamp);
    });
  };

  const currentDevice = devices.find((d) => d.name === selectedDevice) || null;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <Sidebar
        devices={devices}
        onScan={handleScan}
        onAddDevice={handleAddDevice}
        onSelectDevice={handleSelectDevice}
        onToggleEmotionTarget={handleToggleEmotionTarget}
        isScanning={isScanning}
      />

      {/* Main Content */}
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="flex h-14 items-center justify-between border-b border-border bg-card px-6">
          <div className="flex items-center gap-4">
            <h2 className="text-sm font-semibold text-foreground">
              {currentDevice ? currentDevice.label || currentDevice.name : "No Device"}
            </h2>
            {currentDevice && (
              <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                {currentDevice.node_type}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>
              {devices.length} device{devices.length !== 1 ? "s" : ""} connected
            </span>
            {isCameraRunning && (
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                Camera Active
              </span>
            )}
          </div>
        </header>

        {/* Content Grid */}
        <div className="flex-1 overflow-auto p-6">
          <div className="mx-auto max-w-7xl">
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Left Column - Monitoring */}
              <div className="space-y-6 lg:col-span-1">
                <CameraMonitor
                  cameras={cameras}
                  currentCamera={currentCamera}
                  isRunning={isCameraRunning}
                  onStart={handleStartCamera}
                  onStop={handleStopCamera}
                  onSwitch={handleSwitchCamera}
                  onRefreshCameras={refreshCameras}
                />

                <EmotionMonitor
                  reactor={faceData?.reactor || null}
                  perception={faceData?.perception || null}
                  cameraRunning={isCameraRunning}
                />

                <FaceInfo
                  primary={faceData?.primary || null}
                  faces={faceData?.faces || []}
                  cameraRunning={isCameraRunning}
                />
              </div>

              {/* Center Column - Control Panel */}
              <div className="lg:col-span-1">
                <div className="rounded-xl border border-border bg-card">
                  <ControlPanel
                    device={currentDevice}
                    forcedNodeType={forcedNodeType}
                    facePosition={
                      faceData?.primary
                        ? { x: faceData.primary.x, y: faceData.primary.y }
                        : null
                    }
                    isTracking={isCameraRunning && !!faceData?.primary}
                    onOSCSend={handleOSCSend}
                    disabled={!currentDevice}
                  />
                </div>
              </div>

              {/* Right Column - Recorder */}
              <div className="space-y-6 lg:col-span-1">
                <SequenceRecorder
                  onSave={handleSaveSequence}
                  onLoad={handleLoadSequence}
                  onPlay={handlePlaySequence}
                  availableSequences={[]}
                />

                {/* Quick Stats */}
                <div className="rounded-xl border border-border bg-card p-4">
                  <h3 className="mb-3 text-sm font-medium text-foreground">Quick Stats</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg bg-muted/50 p-3 text-center">
                      <span className="text-2xl font-bold text-foreground">
                        {devices.length}
                      </span>
                      <p className="text-xs text-muted-foreground">Devices</p>
                    </div>
                    <div className="rounded-lg bg-muted/50 p-3 text-center">
                      <span className="text-2xl font-bold text-foreground">
                        {emotionTargets.size}
                      </span>
                      <p className="text-xs text-muted-foreground">Auto Targets</p>
                    </div>
                    <div className="rounded-lg bg-muted/50 p-3 text-center">
                      <span className="text-2xl font-bold text-foreground">
                        {faceData?.faces?.length || 0}
                      </span>
                      <p className="text-xs text-muted-foreground">Faces</p>
                    </div>
                    <div className="rounded-lg bg-muted/50 p-3 text-center">
                      <span className="text-2xl font-bold text-foreground">
                        {faceData?.reactor?.flower_emotion?.charAt(0) || "-"}
                      </span>
                      <p className="text-xs text-muted-foreground">Emotion</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
