'use client'

import { AuthProvider } from '@/hooks/useAuth'

export { useAuth } from '@/hooks/useAuth'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      {children}
    </AuthProvider>
  )
}