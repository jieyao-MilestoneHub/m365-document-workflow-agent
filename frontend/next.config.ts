import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV !== "production";
const apiOrigin = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// Content-Security-Policy: allow only what we need. Dev adds 'unsafe-eval' + ws: for HMR.
const csp = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  `connect-src 'self' ${apiOrigin}${isDev ? " ws: http://localhost:*" : ""}`,
  "font-src 'self'",
  "base-uri 'self'",
  "form-action 'self'",
  // allow embedding only as a Microsoft Teams personal tab (no X-Frame-Options, which can't allowlist)
  "frame-ancestors 'self' https://teams.microsoft.com https://*.teams.microsoft.com",
  "object-src 'none'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

const nextConfig: NextConfig = {
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
};

export default nextConfig;
