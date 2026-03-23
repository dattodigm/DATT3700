import { NextResponse } from "next/server";

// In-memory state for demo
let cameraState = {
  running: false,
  index: 0,
};

export async function GET() {
  return NextResponse.json(cameraState);
}

export function setCameraState(state: { running?: boolean; index?: number }) {
  if (state.running !== undefined) cameraState.running = state.running;
  if (state.index !== undefined) cameraState.index = state.index;
}
