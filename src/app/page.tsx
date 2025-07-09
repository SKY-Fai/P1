
'use client'

import { useAuth } from './providers'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import Dashboard from '@/components/Dashboard'
import LoginForm from '@/components/LoginForm'

export default function Home() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && user) {
      // User is authenticated, stay on dashboard
    } else if (!loading && !user) {
      // User is not authenticated, show login
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    )
  }

  if (!user) {
    return <LoginForm />
  }

  return <Dashboard />
}
