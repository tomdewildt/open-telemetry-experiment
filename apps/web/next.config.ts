import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  serverExternalPackages: ["pino"],
  logging: {
    incomingRequests: false,
  },
};

export default nextConfig;
