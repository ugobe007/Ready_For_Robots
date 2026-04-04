/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export: production build has no Node server; `rewrites` apply only to `next dev`.
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // Proxy API to FastAPI so the browser can use same-origin `/api/...` on :3000 (see lib/apiBase.js).
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
