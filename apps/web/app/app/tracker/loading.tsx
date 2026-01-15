/**
 * Tracker Page Loading State
 * 
 * Skeleton loader for application tracker page.
 */

import { TableLoader } from '@/components/ui/loading'
import { Skeleton } from '@/components/ui/skeleton'

export default function TrackerLoading() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Skeleton className="h-8 w-64 mb-2" />
        <Skeleton className="h-5 w-96" />
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-10 w-32" />
      </div>

      {/* Table */}
      <TableLoader rows={8} />
    </div>
  )
}
