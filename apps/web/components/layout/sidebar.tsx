'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { 
  LayoutDashboard,
  FileText,
  Briefcase,
  Target,
  Sparkles,
  MessageSquare,
  ClipboardList,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useUIStore } from '@/store/uiStore'
import { cn } from '@/lib/utils/cn'

const navigation = [
  {
    name: 'Dashboard',
    href: '/app/dashboard',
    icon: LayoutDashboard,
  },
  {
    name: 'Resumes',
    href: '/app/resumes',
    icon: FileText,
  },
  {
    name: 'Jobs',
    href: '/app/jobs',
    icon: Briefcase,
  },
  {
    name: 'Matches',
    href: '/app/matches',
    icon: Target,
  },
  {
    name: 'AI Optimize',
    href: '/app/ai/optimize',
    icon: Sparkles,
  },
  {
    name: 'Interview Prep',
    href: '/app/ai/interview',
    icon: MessageSquare,
  },
  {
    name: 'Tracker',
    href: '/app/tracker',
    icon: ClipboardList,
  },
  {
    name: 'Preferences',
    href: '/app/preferences',
    icon: Settings,
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)
  const hasHydrated = useUIStore((s) => s.hasHydrated)

  // Don't render until hydrated to prevent mismatch
  if (!hasHydrated) {
    return null
  }

  return (
    <>
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      <motion.div
        initial={false}
        animate={{
          width: sidebarOpen ? 256 : 64,
        }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className={cn(
          "fixed left-0 top-0 z-50 h-full bg-card border-r border-border",
          "lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="flex h-full flex-col">
          <div className="flex h-16 items-center justify-between px-4 border-b">
            <motion.div
              initial={false}
              animate={{
                opacity: sidebarOpen ? 1 : 0,
                scale: sidebarOpen ? 1 : 0.8,
              }}
              transition={{ duration: 0.2 }}
              className="flex items-center space-x-2"
            >
              <Zap className="h-8 w-8 text-primary" />
              {sidebarOpen && (
                <span className="text-xl font-bold">JobPilot AI</span>
              )}
            </motion.div>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              className="hidden lg:flex"
            >
              {sidebarOpen ? (
                <ChevronLeft className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          </div>

          <nav className="flex-1 space-y-1 p-4">
            {navigation.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    "hover:bg-accent hover:text-accent-foreground",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground"
                  )}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  <motion.span
                    initial={false}
                    animate={{
                      opacity: sidebarOpen ? 1 : 0,
                      x: sidebarOpen ? 0 : -10,
                    }}
                    transition={{ duration: 0.2 }}
                    className={cn(
                      "ml-3 truncate",
                      !sidebarOpen && "lg:hidden"
                    )}
                  >
                    {item.name}
                  </motion.span>
                </Link>
              )
            })}
          </nav>

          <div className="border-t p-4">
            <motion.div
              initial={false}
              animate={{
                opacity: sidebarOpen ? 1 : 0,
              }}
              transition={{ duration: 0.2 }}
              className={cn(
                "text-xs text-muted-foreground",
                !sidebarOpen && "lg:hidden"
              )}
            >
              <p>© 2024 JobPilot AI</p>
              <p>Free forever</p>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </>
  )
}