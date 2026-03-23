import { NextResponse } from "next/server";
import { generateMockFaceData } from "@/lib/mock-data";

export async function GET() {
  const faceData = generateMockFaceData();
  return NextResponse.json(faceData);
}
