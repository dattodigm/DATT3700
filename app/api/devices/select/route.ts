import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json();
  // In demo mode, we just acknowledge the selection
  return NextResponse.json({ success: true, selected: body.name });
}
