'use client'

import { useRequireAuth } from '@/hooks/useRequireAuth'
import { Sidebar } from '@/components/layout/sidebar'
import { Topbar } from '@/components/layout/topbar'
import { useUIStore } from '@/store/uiStore'
import { cn } from '@/lib/utils/cn'

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isAuthenticated, isLoading } = useRequireAuth()
  
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const hasHydrated = useUIStore((s) => s.hasHydrated)

  // Wait until zustand finishes reading localStorage
  if (!hasHydrated) {
    return <div className="min-h-screen bg-background" suppressHydrationWarning />
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  // Never return null (tree mismatch). Show stable shell.
  if (!isAuthenticated) {
    return <div className="min-h-screen bg-background" />
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div
        className={cn(
          "transition-all duration-300 ease-in-out",
          sidebarOpen ? "lg:ml-64" : "lg:ml-16"
        )}
      >
        <Topbar />
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  )
}