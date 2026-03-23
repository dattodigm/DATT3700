// Node Types based on device_registry.json
export type NodeType = "kait" | "sue" | "sylvie" | "face_track" | "unknown";

export interface Device {
  name: string;
  ip: string;
  port: number;
  node_type: NodeType;
  label: string;
  source: "manual" | "mdns" | "gateway_self" | "gateway_client";
  emotion_enabled: boolean;
  metadata?: Record<string, unknown>;
}

export interface CameraState {
  running: boolean;
  index: number;
}

export interface FaceData {
  x: number;
  y: number;
  w: number;
  h: number;
  confidence: number;
}

export interface PerceptionData {
  vit_emotion?: {
    scores: number[];
    classes: string[];
    top_emotion?: string;
  };
  emotion?: {
    scores: Record<string, number>;
    dominant?: string;
  };
}

export interface ReactorState {
  flower_emotion: "BLOOM" | "ALERT" | "SOOTHE" | "REST";
  source_emotion: string;
  source_confidence: number;
  source_model: string;
  stability: number;
}

export interface FaceAPIResponse {
  camera_running: boolean;
  primary: FaceData | null;
  faces: FaceData[];
  perception: PerceptionData | null;
  reactor: ReactorState | null;
}

// Control Mode
export type ControlMode = "auto" | "manual" | "tracking";

// Motion Sequence Recording
export interface SequenceEvent {
  timestamp: number;
  type: "motor" | "led" | "servo" | "preset" | "motion";
  target?: string;
  address: string;
  args: (number | string)[];
}

export interface MotionSequence {
  label: string;
  name: string;
  duration: number;
  events: SequenceEvent[];
  created_at: string;
}

// Preset motion modes for Kait node
export interface MotionPreset {
  id: number;
  name: string;
  description: string;
  duration: number;
}

export const KAIT_MOTION_PRESETS: MotionPreset[] = [
  { id: 1, name: "Gentle Sway", description: "Slow back-and-forth", duration: 3000 },
  { id: 2, name: "Fast Spin", description: "Continuous rotation", duration: 2000 },
  { id: 3, name: "Pulse Vibrate", description: "Rapid trembling", duration: 1000 },
  { id: 4, name: "Accelerate Spin", description: "Gradually speed up", duration: 3000 },
  { id: 5, name: "Smooth Brake", description: "Slow deceleration", duration: 1500 },
  { id: 6, name: "Pulse Start", description: "Burst startup", duration: 2000 },
];

// Sue node state presets
export interface SueStatePreset {
  id: string;
  name: string;
  description: string;
  ledR: number;
  ledG: number;
}

export const SUE_STATE_PRESETS: SueStatePreset[] = [
  { id: "danger", name: "Danger", description: "Red LED + Close", ledR: 255, ledG: 0 },
  { id: "relax", name: "Relax", description: "Green LED + Open", ledR: 0, ledG: 255 },
  { id: "idle", name: "Idle", description: "All off + Close", ledR: 0, ledG: 0 },
  { id: "alert", name: "Alert", description: "Both LEDs + Half", ledR: 255, ledG: 255 },
  { id: "calm", name: "Calm", description: "Green + Slow open", ledR: 0, ledG: 255 },
  { id: "breathe", name: "Breathe", description: "Open then auto-close", ledR: 0, ledG: 255 },
];

// Sylvie presets
export interface SylviePreset {
  id: number;
  name: string;
  description: string;
}

export const SYLVIE_PRESETS: SylviePreset[] = [
  { id: 1, name: "Bloom", description: "Yellow LED + Motors spin" },
  { id: 2, name: "Stress", description: "Red blink + Motors twitch" },
  { id: 3, name: "Rest", description: "All stopped" },
  { id: 4, name: "Calm", description: "Purple LED + Slow spin" },
];

// Reactor config
export interface ReactorConfig {
  enter_th: number;
  exit_th: number;
  decay: number;
  shock_scale: number;
  bloom_gain: number;
  alert_gain: number;
  soothe_gain: number;
  hold_soothe_ms: number;
}

// Tracking config
export interface TrackingConfig {
  enabled: boolean;
  transport: "osc" | "serial";
  rate_hz: number;
  deadband: number;
  frame_width: number;
  frame_height: number;
}
