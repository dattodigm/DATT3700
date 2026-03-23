import type { Device, FaceAPIResponse, MotionSequence } from "./types";

// Mock devices for offline testing
export const MOCK_DEVICES: Device[] = [
  {
    name: "kait-flower-01",
    ip: "192.168.1.101",
    port: 8000,
    node_type: "kait",
    label: "Kait Flower Alpha",
    source: "mdns",
    emotion_enabled: true,
  },
  {
    name: "sue-petal-01",
    ip: "192.168.1.102",
    port: 8000,
    node_type: "sue",
    label: "Sue Petal Beta",
    source: "mdns",
    emotion_enabled: false,
  },
  {
    name: "sylvie-bloom-01",
    ip: "192.168.1.103",
    port: 8000,
    node_type: "sylvie",
    label: "Sylvie Bloom Gamma",
    source: "gateway_client",
    emotion_enabled: true,
  },
  {
    name: "tracker-01",
    ip: "192.168.1.104",
    port: 8000,
    node_type: "face_track",
    label: "Face Tracker Delta",
    source: "manual",
    emotion_enabled: false,
  },
];

// Generate mock face data with random variation
export function generateMockFaceData(): FaceAPIResponse {
  const hasFace = Math.random() > 0.2;
  const emotionClasses = ["anger", "disgust", "fear", "happiness", "neutral", "sadness", "surprise"];
  const randomScores = emotionClasses.map(() => Math.random());
  const total = randomScores.reduce((a, b) => a + b, 0);
  const normalizedScores = randomScores.map((s) => s / total);
  const topIndex = normalizedScores.indexOf(Math.max(...normalizedScores));
  
  const flowerEmotions = ["BLOOM", "ALERT", "SOOTHE", "REST"] as const;
  const randomFlowerEmotion = flowerEmotions[Math.floor(Math.random() * flowerEmotions.length)];

  return {
    camera_running: true,
    primary: hasFace
      ? {
          x: 0.3 + Math.random() * 0.4,
          y: 0.3 + Math.random() * 0.4,
          w: 0.15 + Math.random() * 0.1,
          h: 0.2 + Math.random() * 0.1,
          confidence: 0.7 + Math.random() * 0.3,
        }
      : null,
    faces: hasFace
      ? [
          {
            x: 0.3 + Math.random() * 0.4,
            y: 0.3 + Math.random() * 0.4,
            w: 0.15 + Math.random() * 0.1,
            h: 0.2 + Math.random() * 0.1,
            confidence: 0.7 + Math.random() * 0.3,
          },
        ]
      : [],
    perception: {
      vit_emotion: {
        scores: normalizedScores,
        classes: emotionClasses,
        top_emotion: emotionClasses[topIndex],
      },
    },
    reactor: {
      flower_emotion: randomFlowerEmotion,
      source_emotion: emotionClasses[topIndex],
      source_confidence: normalizedScores[topIndex],
      source_model: "vit_emotion",
      stability: 0.5 + Math.random() * 0.5,
    },
  };
}

// Mock saved sequences
export const MOCK_SEQUENCES: MotionSequence[] = [
  {
    label: "happiness",
    name: "Happy Dance",
    duration: 5000,
    events: [
      { timestamp: 0, type: "motor", address: "/kait/motor/speed", args: [200], target: "kait-flower-01" },
      { timestamp: 1000, type: "preset", address: "/kait/motion/preset", args: [1], target: "kait-flower-01" },
      { timestamp: 2500, type: "motor", address: "/kait/motor/speed", args: [-200], target: "kait-flower-01" },
      { timestamp: 4000, type: "motor", address: "/kait/motor/speed", args: [0], target: "kait-flower-01" },
    ],
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    label: "sadness",
    name: "Sad Droop",
    duration: 8000,
    events: [
      { timestamp: 0, type: "led", address: "/sue/led/r", args: [0], target: "sue-petal-01" },
      { timestamp: 0, type: "led", address: "/sue/led/g", args: [50], target: "sue-petal-01" },
      { timestamp: 500, type: "servo", address: "/sue/servo/angle", args: [30], target: "sue-petal-01" },
      { timestamp: 4000, type: "servo", address: "/sue/servo/angle", args: [10], target: "sue-petal-01" },
    ],
    created_at: new Date(Date.now() - 172800000).toISOString(),
  },
  {
    label: "anger",
    name: "Angry Shake",
    duration: 3000,
    events: [
      { timestamp: 0, type: "preset", address: "/sylvie/preset", args: [2], target: "sylvie-bloom-01" },
      { timestamp: 1500, type: "motor", address: "/sylvie/motor/A/speed", args: [255], target: "sylvie-bloom-01" },
      { timestamp: 1600, type: "motor", address: "/sylvie/motor/A/speed", args: [-255], target: "sylvie-bloom-01" },
      { timestamp: 1700, type: "motor", address: "/sylvie/motor/A/speed", args: [255], target: "sylvie-bloom-01" },
      { timestamp: 1800, type: "motor", address: "/sylvie/motor/A/speed", args: [0], target: "sylvie-bloom-01" },
    ],
    created_at: new Date(Date.now() - 259200000).toISOString(),
  },
];

// Check if we're in demo/mock mode
export function isDemoMode(): boolean {
  if (typeof window === "undefined") return true;
  return (
    process.env.NEXT_PUBLIC_DEMO_MODE === "true" ||
    window.location.search.includes("demo=true")
  );
}
