/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    BASEURL: process.env.BASEURL,
    STRIPE_PUBLIC: process.env.STRIPE_PUBLIC,
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "aec18cb39d6670d41651478c21c17654.r2.cloudflarestorage.com",
      },
    ],
  },
};

// module.exports = nextConfig;

const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

module.exports = withBundleAnalyzer(nextConfig);
