/** @type {import('next').NextConfig} */
const nextConfig = {
  // Removed 'output: export' to enable server-side rendering (getServerSideProps)
  // This allows instant page loads with pre-rendered data snapshot
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
