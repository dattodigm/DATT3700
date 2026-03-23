import { NextResponse } from "next/server";

export async function GET() {
  // Return mock camera list
  return NextResponse.json({ cameras: [0, 1, 2] });
}
