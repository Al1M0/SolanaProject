import type { NextConfig } from "next";
const config: NextConfig = {
  allowedDevOrigins: ["terminal.local"],
  output: process.env.STATIC_EXPORT === "1" ? "export" : "standalone",
  trailingSlash: true,
  images: { unoptimized: true },
  turbopack: {root: process.cwd()},
};
if (process.env.STATIC_EXPORT !== "1" && process.env.NEXT_DEV_CHAIN_PROXY) {
  config.rewrites = async () => {
    return [{source: "/api/:path*", destination: process.env.NEXT_DEV_CHAIN_PROXY + "/api/:path*"}];
  };
}
export default config;
