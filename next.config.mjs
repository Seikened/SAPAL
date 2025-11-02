// next.config.mjs
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: { turbo: { rules: {} } },
  async rewrites() {
    return [
      { source: '/sim/:path*', destination: 'http://localhost:8000/sim/:path*' },
      { source: '/health', destination: 'http://localhost:8000/health' },
    ];
  },
  // quita el warning de dev multi-origen en LAN
  allowedDevOrigins: ['http://localhost:3000', 'http://192.168.100.5:3000'],
};
export default nextConfig;