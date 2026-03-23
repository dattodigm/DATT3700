"use client";

import { create } from "zustand";
import type {
  Device,
  ControlMode,
  SequenceEvent,
  MotionSequence,
  NodeType,
} from "./types";

interface AppState {
  // Devices
  devices: Device[];
  selectedDevice: string | null;
  emotionTargets: Set<string>;
  
  // Control mode
  controlMode: ControlMode;
  
  // Recording state
  isRecording: boolean;
  recordStartTime: number;
  recordedEvents: SequenceEvent[];
  currentSequenceLabel: string;
  currentSequenceName: string;
  
  // Loaded sequence for playback
  loadedSequence: MotionSequence | null;
  isPlaying: boolean;
  playbackProgress: number;
  
  // UI state
  sidebarOpen: boolean;
  activePanel: "nodes" | "sequences" | "settings";
  forcedNodeType: NodeType | null;
  
  // Actions
  setDevices: (devices: Device[]) => void;
  selectDevice: (name: string | null) => void;
  toggleEmotionTarget: (name: string) => void;
  setEmotionTargets: (names: string[]) => void;
  setControlMode: (mode: ControlMode) => void;
  
  // Recording actions
  startRecording: () => void;
  stopRecording: () => SequenceEvent[];
  addRecordedEvent: (event: Omit<SequenceEvent, "timestamp">) => void;
  setSequenceLabel: (label: string) => void;
  setSequenceName: (name: string) => void;
  
  // Playback actions
  loadSequence: (sequence: MotionSequence) => void;
  startPlayback: () => void;
  stopPlayback: () => void;
  setPlaybackProgress: (progress: number) => void;
  
  // UI actions
  toggleSidebar: () => void;
  setActivePanel: (panel: "nodes" | "sequences" | "settings") => void;
  setForcedNodeType: (type: NodeType | null) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  devices: [],
  selectedDevice: null,
  emotionTargets: new Set(),
  controlMode: "manual",
  isRecording: false,
  recordStartTime: 0,
  recordedEvents: [],
  currentSequenceLabel: "",
  currentSequenceName: "",
  loadedSequence: null,
  isPlaying: false,
  playbackProgress: 0,
  sidebarOpen: true,
  activePanel: "nodes",
  forcedNodeType: null,

  // Device actions
  setDevices: (devices) => set({ devices }),
  
  selectDevice: (name) => set({ selectedDevice: name }),
  
  toggleEmotionTarget: (name) =>
    set((state) => {
      const newTargets = new Set(state.emotionTargets);
      if (newTargets.has(name)) {
        newTargets.delete(name);
      } else {
        newTargets.add(name);
      }
      return { emotionTargets: newTargets };
    }),
  
  setEmotionTargets: (names) =>
    set({ emotionTargets: new Set(names) }),
  
  setControlMode: (mode) => set({ controlMode: mode }),

  // Recording actions
  startRecording: () =>
    set({
      isRecording: true,
      recordStartTime: Date.now(),
      recordedEvents: [],
    }),
  
  stopRecording: () => {
    const events = get().recordedEvents;
    set({
      isRecording: false,
      recordStartTime: 0,
    });
    return events;
  },
  
  addRecordedEvent: (event) =>
    set((state) => {
      if (!state.isRecording) return state;
      const timestamp = Date.now() - state.recordStartTime;
      return {
        recordedEvents: [
          ...state.recordedEvents,
          { ...event, timestamp },
        ],
      };
    }),
  
  setSequenceLabel: (label) => set({ currentSequenceLabel: label }),
  setSequenceName: (name) => set({ currentSequenceName: name }),

  // Playback actions
  loadSequence: (sequence) => set({ loadedSequence: sequence }),
  
  startPlayback: () => set({ isPlaying: true, playbackProgress: 0 }),
  
  stopPlayback: () => set({ isPlaying: false, playbackProgress: 0 }),
  
  setPlaybackProgress: (progress) => set({ playbackProgress: progress }),

  // UI actions
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  
  setActivePanel: (panel) => set({ activePanel: panel }),
  
  setForcedNodeType: (type) => set({ forcedNodeType: type }),
}));
