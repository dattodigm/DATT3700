import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json();
  // Simulate scan delay
  await new Promise((resolve) => setTimeout(resolve, 1500));
  
  return NextResponse.json({
    success: true,
    mode: body.mode,
    found: Math.floor(Math.random() * 3) + 1,
  });
}
