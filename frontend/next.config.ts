import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Allow a local production check without overwriting a running dev server's output.
  distDir: process.env.FRONTEND_BUILD_DIR || '.next',
};

export default nextConfig;
