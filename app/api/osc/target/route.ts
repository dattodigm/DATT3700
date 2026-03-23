import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json();
  return NextResponse.json({
    success: true,
    device: {
      name: body.name,
      ip: body.ip,
      port: body.port,
      node_type: body.node_type,
    },
  });
}
