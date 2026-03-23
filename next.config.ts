import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow cross-origin requests to the Flask backend
  async rewrites() {
    const backendUrl = process.env.FLASK_BACKEND_URL || "http://localhost:5000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: "/video_feed",
        destination: `${backendUrl}/video_feed`,
      },
    ];
  },
};

export default nextConfig;
