/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export: no Next.js /api routes. Client code must use getApiBase() + NEXT_PUBLIC_API_URL.
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
