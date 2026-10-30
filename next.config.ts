import type { NextConfig } from "next";
const nextConfig: NextConfig = {
  output: "export",
  basePath: "/BFR-AMS2",
  images: { unoptimized: true },
  trailingSlash: true,
};
export default nextConfig;
