/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',       // static HTML/CSS/JS — no Node server needed
  trailingSlash: true,    // /admin → /admin/index.html (clean file paths)
  images: {
    unoptimized: true,    // required for static export
  },
};

module.exports = nextConfig;
