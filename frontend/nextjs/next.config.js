/** @type {import('next').NextConfig} */
// `output: 'export'` and `rewrites()` together make Next warn: rewrites don't apply to static export.
// Dev: no `export` + rewrites → proxy `/api/*` to FastAPI on :8000. Build: `export`, no rewrites.
const isDev = process.env.NODE_ENV === 'development';

const nextConfig = {
  ...(!isDev ? { output: 'export' } : {}),
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // Only attach `rewrites` in dev — if the key exists, `next build` warns even when it returns [].
  ...(isDev
    ? {
        async rewrites() {
          return [
            {
              source: '/api/:path*',
              destination: 'http://127.0.0.1:8000/api/:path*',
            },
          ];
        },
      }
    : {}),
};

module.exports = nextConfig;
