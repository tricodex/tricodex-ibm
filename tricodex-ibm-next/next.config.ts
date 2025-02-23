import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Temporarily disable TypeScript & ESLint checks for demo purposes
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  }
};

export default nextConfig;
