import { NextResponse } from "next/server";
import { MOCK_DEVICES } from "@/lib/mock-data";

// In-memory state for demo mode
let devices = [...MOCK_DEVICES];
let selectedDevice: string | null = "kait-flower-01";
let emotionTargets: string[] = ["kait-flower-01", "sylvie-bloom-01"];

export async function GET() {
  return NextResponse.json({
    devices,
    selected: selectedDevice,
    emotion_targets: emotionTargets,
  });
}

export async function POST(request: Request) {
  const body = await request.json();
  
  if (body.action === "select") {
    selectedDevice = body.name;
  } else if (body.action === "emotion_targets") {
    emotionTargets = body.names || [];
  } else if (body.action === "add") {
    const newDevice = {
      name: body.name,
      ip: body.ip,
      port: body.port,
      node_type: body.node_type,
      label: body.label || body.name,
      source: "manual" as const,
      emotion_enabled: false,
    };
    devices.push(newDevice);
  }
  
  return NextResponse.json({ success: true });
}
