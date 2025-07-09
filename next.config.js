
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Production optimizations
  poweredByHeader: false,
  compress: true,
  
  // API rewrites for Flask backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'production' 
          ? 'https://your-flask-backend.replit.app/api/:path*'
          : 'http://0.0.0.0:5001/api/:path*',
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
    ]
  },

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

  // Experimental features
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['react-bootstrap', 'bootstrap'],
  },

  // Output configuration for static export if needed
  output: 'standalone',
  
  // Environment variables
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://0.0.0.0:5001',
  }
}

module.exports = nextConfig
