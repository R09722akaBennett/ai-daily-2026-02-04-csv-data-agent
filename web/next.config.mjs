/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // react-pdf ships .mjs and references `canvas` as an optional dep; mark it
  // external so Webpack stops trying to bundle a Node-only module.
  webpack: (config) => {
    config.resolve.alias.canvas = false;
    return config;
  },
};

export default nextConfig;
