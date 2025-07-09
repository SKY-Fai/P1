
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5001/api/:path*', // Python Flask API server
      },
      {
        source: '/auth/:path*',
        destination: 'http://localhost:5001/auth/:path*',
      },
      {
        source: '/admin/:path*',
        destination: 'http://localhost:5001/admin/:path*',
      }
    ]
  },
  images: {
    domains: ['localhost'],
  },
  experimental: {
    esmExternals: false,
  }
}

module.exports = nextConfig
