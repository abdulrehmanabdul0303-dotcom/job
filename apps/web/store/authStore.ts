import { create } from 'zustand'
import { getCurrentUser, type User } from '@/lib/auth'

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  
  // Actions
  setUser: (user: User | null) => void
  setLoading: (loading: boolean) => void
  checkAuth: () => Promise<void>
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  setUser: (user) => set({ 
    user, 
    isAuthenticated: !!user,
    isLoading: false 
  }),

  setLoading: (loading) => set({ isLoading: loading }),

  checkAuth: async () => {
    try {
      set({ isLoading: true })
      // The api() function will automatically handle 401 and refresh tokens
      const user = await getCurrentUser()
      set({ 
        user, 
        isAuthenticated: true, 
        isLoading: false 
      })
    } catch (error) {
      // Not authenticated or refresh failed
      set({ 
        user: null, 
        isAuthenticated: false, 
        isLoading: false 
      })
      // Don't log error in production - it's normal for users to not be authenticated
      if (process.env.NODE_ENV === 'development') {
        console.log('Auth check failed (normal if not logged in):', error)
      }
    }
  },

  clearAuth: () => set({ 
    user: null, 
    isAuthenticated: false, 
    isLoading: false 
  }),
}))