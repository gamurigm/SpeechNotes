import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: "C:\\Users\\gamur\\OneDrive - UNIVERSIDAD DE LAS FUERZAS ARMADAS ESPE\\ESPE VI NIVEL SII2025\\Analisis y Diseño\\p",
  } as any,
  async rewrites() {
    return [
      {
        source: '/api/:path((?!auth).*)',
        destination: 'http://127.0.0.1:8001/api/:path*',
      },
    ];
  },
};

export default nextConfig;
