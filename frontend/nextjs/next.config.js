/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export: no Next.js /api routes. Do not use `rewrites` here — Next warns they are ignored
  // for `output: 'export'` builds; use `getApiBase()` → FastAPI directly in dev (CORS on backend).
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
