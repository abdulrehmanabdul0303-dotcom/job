/**
 * Matches Page Loading State
 * 
 * Skeleton loader for job matches page.
 */

import { MatchCardLoader } from '@/components/ui/loading'

export default function MatchesLoading() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <div className="h-8 w-56 bg-gray-200 rounded animate-pulse mb-2"></div>
        <div className="h-4 w-80 bg-gray-200 rounded animate-pulse"></div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <MatchCardLoader />
        <MatchCardLoader />
        <MatchCardLoader />
        <MatchCardLoader />
      </div>
    </div>
  )
}
