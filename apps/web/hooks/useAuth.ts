import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { login as authLogin, register as authRegister, logout as authLogout } from '@/lib/auth'
import { toast } from './use-toast'

export function useAuth() {
  const router = useRouter()
  const { user, isLoading, isAuthenticated, setUser, setLoading, checkAuth, clearAuth } = useAuthStore()

  // Check authentication status on mount
  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  const login = async (email: string, password: string) => {
    try {
      setLoading(true)
      await authLogin(email, password)
      
      // After successful login, check auth to get user data
      await checkAuth()
      
      toast({
        title: "Welcome back!",
        description: "You have been successfully logged in.",
        variant: "default",
      })

      // Redirect to dashboard or intended page
      const redirect = new URLSearchParams(window.location.search).get('redirect')
      router.push(redirect || '/app/dashboard')
    } catch (error: any) {
      setLoading(false)
      toast({
        title: "Login Failed",
        description: error.message || "Invalid credentials. Please try again.",
        variant: "destructive",
      })
      throw error
    }
  }

  const register = async (email: string, password: string, full_name?: string) => {
    try {
      setLoading(true)
      await authRegister(email, password, full_name)
      
      // After successful registration, check auth to get user data
      await checkAuth()
      
      toast({
        title: "Account Created!",
        description: "Welcome to JobPilot AI. Let's get started!",
        variant: "default",
      })

      router.push('/app/dashboard')
    } catch (error: any) {
      setLoading(false)
      toast({
        title: "Registration Failed",
        description: error.message || "Failed to create account. Please try again.",
        variant: "destructive",
      })
      throw error
    }
  }

  const logout = async () => {
    try {
      await authLogout()
    } catch (error) {
      console.warn("Logout request failed:", error)
    } finally {
      clearAuth()
      
      toast({
        title: "Logged Out",
        description: "You have been successfully logged out.",
        variant: "default",
      })

      router.push('/login')
    }
  }

  return {
    // State
    user,
    isAuthenticated,
    isLoading,
    
    // Actions
    login,
    register,
    logout,
    checkAuth,
  }
}