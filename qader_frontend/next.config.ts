import createNextIntlPlugin from "next-intl/plugin";

// Adjust the path if your i18n.ts is elsewhere, but './src/i18n.ts' is common
// if next.config.ts is in the root and i18n.ts is in src/.
// Since your i18n.ts is at 'src/i18n.ts', this path should be correct.
const withNextIntl = createNextIntlPlugin("./src/i18n.ts");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // ... any other Next.js configurations you have
  // Example: if you have experimental features or webpack customizations
  // experimental: {
  //   typedRoutes: true, // Example
  // },
};

export default withNextIntl(nextConfig);
