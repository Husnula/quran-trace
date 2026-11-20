import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",        // Static export untuk Cloudflare Pages
  trailingSlash: true,     // CF Pages butuh trailing slash
  images: {
    unoptimized: true,     // Static export tidak support next/image optimizer
  },
};

export default nextConfig;
