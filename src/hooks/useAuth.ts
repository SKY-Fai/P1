
'use client'

import { useState, useEffect, createContext, useContext, ReactNode } from 'react'
import { apiClient, endpoints } from '@/lib/api'
import { User, AuthState } from '@/types'

interface AuthContextType extends AuthState {
  login: (credentials: { username: string; password: string }) => Promise<boolean>
  logout: () => Promise<void>
  register: (data: { name: string; email: string; password: string }) => Promise<void>
  updateUser: (userData: Partial<User>) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  })

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('authToken')
      if (!token) {
        setAuthState(prev => ({ ...prev, isLoading: false }))
        return
      }

      const response = await apiClient.get<User>(endpoints.auth.profile)
      setAuthState({
        user: response.data,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      localStorage.removeItem('authToken')
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      })
    }
  }

  const login = async (credentials: { username: string; password: string }) => {
    try {
      const response = await apiClient.post<{ user: User; token: string }>(endpoints.auth.login, {
        username: credentials.username,
        password: credentials.password,
      })

      localStorage.setItem('authToken', response.data.token)
      setAuthState({
        user: response.data.user,
        isAuthenticated: true,
        isLoading: false,
      })
      return true
    } catch (error) {
      return false
    }
  }

  const logout = async () => {
    try {
      await apiClient.post(endpoints.auth.logout)
    } catch (error) {
      // Handle logout error if needed
    } finally {
      localStorage.removeItem('authToken')
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      })
    }
  }

  const register = async (data: { name: string; email: string; password: string }) => {
    try {
      const response = await apiClient.post<{ user: User; token: string }>(endpoints.auth.register, data)

      localStorage.setItem('authToken', response.data.token)
      setAuthState({
        user: response.data.user,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      throw error
    }
  }

  const updateUser = (userData: Partial<User>) => {
    setAuthState(prev => ({
      ...prev,
      user: prev.user ? { ...prev.user, ...userData } : null,
    }))
  }

  return (
    <AuthContext.Provider
      value={{
        ...authState,
        login,
        logout,
        register,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
