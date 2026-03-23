import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json();
  
  // Log OSC command for demo purposes
  console.log("[Demo OSC]", body.address, body.args, "->", body.target);
  
  return NextResponse.json({
    success: true,
    address: body.address,
    args: body.args,
    target: body.target,
  });
}
