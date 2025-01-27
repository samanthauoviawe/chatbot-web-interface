import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;

// next.config.ts
module.exports = {
  reactStrictMode: true,
  experimental: {
    appDir: true, // Enable the App Router (this is needed for Next.js 13+)
  },
};

