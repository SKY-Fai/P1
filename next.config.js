/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    optimizeCss: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
    BACKEND_URL: process.env.BACKEND_URL || 'http://0.0.0.0:5001',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5000/api/:path*',
      },
      {
        source: '/auth/:path*',
        destination: process.env.NODE_ENV === 'production'
          ? 'https://your-flask-backend.replit.app/auth/:path*'
          : 'http://0.0.0.0:5001/auth/:path*',
      },
      {
        source: '/admin/:path*',
        destination: process.env.NODE_ENV === 'production'
          ? 'https://your-flask-backend.replit.app/admin/:path*'
          : 'http://0.0.0.0:5001/admin/:path*',
      }
    ];
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
    // Production optimizations
    poweredByHeader: false,
    compress: true,
  // Headers for security and performance
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

  // Image optimization
  images: {
    domains: ['localhost', '*.replit.app', '*.replit.dev'],
    formats: ['image/webp', 'image/avif'],
  },
  // Output configuration for static export if needed
  output: 'standalone',
};

module.exports = nextConfig;