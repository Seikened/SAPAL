// next.config.mjs
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      { source: '/sim/:path*', destination: 'http://backend:8000/sim/:path*' },
      { source: '/health',     destination: 'http://backend:8000/health' },
    ];
  },
  allowedDevOrigins: ['http://localhost:3000', 'http://192.168.100.5:3000'],
};
export default nextConfig;