/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',       // static HTML/CSS/JS — fast, no Node server needed
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
