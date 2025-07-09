
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    optimizeCss: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://0.0.0.0:5001',
    BACKEND_URL: process.env.BACKEND_URL || 'http://0.0.0.0:5001',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://0.0.0.0:5001/api/:path*',
      },
      {
        source: '/auth/:path*',
        destination: 'http://0.0.0.0:5001/auth/:path*',
      },
      {
        source: '/admin/:path*',
        destination: 'http://0.0.0.0:5001/admin/:path*',
      }
    ];
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
  poweredByHeader: false,
  compress: true,
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          }
        ],
      },
    ]
  },
  images: {
    domains: ['localhost', '*.replit.app', '*.replit.dev'],
    formats: ['image/webp', 'image/avif'],
  },
  output: 'standalone',
};

module.exports = nextConfig;
