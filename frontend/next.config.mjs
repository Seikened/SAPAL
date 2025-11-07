const nextConfig = {
  async rewrites() {
    return [
      { source: '/sim/:path*', destination: 'http://backend:8000/sim/:path*' },
      { source: '/health',     destination: 'http://backend:8000/health' },
    ];
  },
  allowedDevOrigins: [
    'http://localhost:3000',
    'http://192.168.100.5:3000',
    'https://dashboard-sapal-vaqcb1-4e8607-89-116-212-100.traefik.me',
    'http://dashboard-sapal-vaqcb1-4e8607-89-116-212-100.traefik.me'
  ],
};
export default nextConfig;