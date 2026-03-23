import { NextResponse } from "next/server";

// In-memory state for demo
const cameraState = {
  running: false,
  index: 0,
};

export async function GET() {
  return NextResponse.json(cameraState);
}

export async function POST(request: Request) {
  const body = await request.json();
  if (body.running !== undefined) cameraState.running = body.running;
  if (body.index !== undefined) cameraState.index = body.index;
  return NextResponse.json(cameraState);
}
