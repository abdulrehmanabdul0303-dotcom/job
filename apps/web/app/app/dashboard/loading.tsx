/**
 * Dashboard Loading State
 * 
 * Skeleton loader for dashboard page.
 */

import { CardLoader } from '@/components/ui/loading'

export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div className="h-9 w-48 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-10 w-24 bg-gray-200 rounded animate-pulse"></div>
        </div>

        {/* Cards Grid */}
        <div className="grid gap-6 md:grid-cols-2">
          <CardLoader />
          <CardLoader />
        </div>

        {/* Debug Card */}
        <div className="mt-6">
          <CardLoader />
        </div>
      </div>
    </div>
  )
}
