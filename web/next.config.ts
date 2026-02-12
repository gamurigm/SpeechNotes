import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path((?!auth).*)',
        destination: `${process.env.API_URL || 'http://127.0.0.1:8001'}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
