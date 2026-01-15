import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIState {
  // Sidebar state
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void

  // Theme state (handled by next-themes, but we can track preference)
  theme: 'light' | 'dark' | 'system'
  setTheme: (theme: 'light' | 'dark' | 'system') => void

  // Loading states
  isLoading: boolean
  setIsLoading: (loading: boolean) => void

  // Upload progress
  uploadProgress: number
  setUploadProgress: (progress: number) => void

  // Wizard state for multi-step forms
  wizardStep: number
  setWizardStep: (step: number) => void
  resetWizard: () => void

  // Modal states
  modals: {
    shareLink: boolean
    deleteConfirm: boolean
    uploadResume: boolean
  }
  openModal: (modal: keyof UIState['modals']) => void
  closeModal: (modal: keyof UIState['modals']) => void
  closeAllModals: () => void

  // Toast state (for custom toast system if needed)
  toasts: Array<{
    id: string
    title: string
    description?: string
    variant: 'default' | 'destructive' | 'success'
  }>
  addToast: (toast: Omit<UIState['toasts'][0], 'id'>) => void
  removeToast: (id: string) => void

  // Hydration state
  hasHydrated: boolean
  setHasHydrated: (v: boolean) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      // Sidebar
      sidebarOpen: false,
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      // Theme
      theme: 'system',
      setTheme: (theme) => set({ theme }),

      // Loading
      isLoading: false,
      setIsLoading: (loading) => set({ isLoading: loading }),

      // Upload progress
      uploadProgress: 0,
      setUploadProgress: (progress) => set({ uploadProgress: progress }),

      // Wizard
      wizardStep: 0,
      setWizardStep: (step) => set({ wizardStep: step }),
      resetWizard: () => set({ wizardStep: 0 }),

      // Modals
      modals: {
        shareLink: false,
        deleteConfirm: false,
        uploadResume: false,
      },
      openModal: (modal) =>
        set((state) => ({
          modals: { ...state.modals, [modal]: true },
        })),
      closeModal: (modal) =>
        set((state) => ({
          modals: { ...state.modals, [modal]: false },
        })),
      closeAllModals: () =>
        set({
          modals: {
            shareLink: false,
            deleteConfirm: false,
            uploadResume: false,
          },
        }),

      // Toasts
      toasts: [],
      addToast: (toast) =>
        set((state) => ({
          toasts: [
            ...state.toasts,
            { ...toast, id: Math.random().toString(36).substr(2, 9) },
          ],
        })),
      removeToast: (id) =>
        set((state) => ({
          toasts: state.toasts.filter((toast) => toast.id !== id),
        })),

      // Hydration
      hasHydrated: false,
      setHasHydrated: (v) => set({ hasHydrated: v }),
    }),
    {
      name: 'jobpilot-ui-store',
      partialize: (state) => ({
        theme: state.theme,
        sidebarOpen: state.sidebarOpen,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true)
      },
    }
  )
)