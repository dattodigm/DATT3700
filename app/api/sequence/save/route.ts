import { NextResponse } from "next/server";
import type { MotionSequence } from "@/lib/types";

// In-memory storage for demo
const savedSequences: MotionSequence[] = [];

export async function POST(request: Request) {
  const sequence: MotionSequence = await request.json();
  
  // Add or update sequence
  const existingIndex = savedSequences.findIndex(
    (s) => s.name === sequence.name && s.label === sequence.label
  );
  
  if (existingIndex >= 0) {
    savedSequences[existingIndex] = sequence;
  } else {
    savedSequences.push(sequence);
  }
  
  return NextResponse.json({ success: true, sequence });
}

export { savedSequences };
