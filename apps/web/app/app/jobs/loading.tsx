/**
 * Jobs Page Loading State
 * 
 * Skeleton loader for jobs search page.
 */

import { JobCardLoader } from '@/components/ui/loading'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

export default function JobsLoading() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <Skeleton className="h-9 w-64 mb-2" />
        <Skeleton className="h-5 w-96" />
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-4">
            <div className="md:col-span-2">
              <Skeleton className="h-10 w-full" />
            </div>
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div className="mt-4">
            <Skeleton className="h-5 w-32" />
          </div>
        </CardContent>
      </Card>

      {/* Results Header */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-5 w-40" />
      </div>

      {/* Job Cards */}
      <div className="space-y-4">
        <JobCardLoader />
        <JobCardLoader />
        <JobCardLoader />
        <JobCardLoader />
        <JobCardLoader />
      </div>
    </div>
  )
}
