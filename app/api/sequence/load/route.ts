import { NextResponse } from "next/server";
import { MOCK_SEQUENCES } from "@/lib/mock-data";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const name = searchParams.get("name");
  
  if (!name) {
    // Return all sequences
    return NextResponse.json({ sequences: MOCK_SEQUENCES });
  }
  
  const sequence = MOCK_SEQUENCES.find((s) => s.name === name);
  
  if (!sequence) {
    return NextResponse.json({ error: "Sequence not found" }, { status: 404 });
  }
  
  return NextResponse.json({ sequence });
}
