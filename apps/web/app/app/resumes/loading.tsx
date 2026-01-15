/**
 * Resumes Page Loading State
 * 
 * Skeleton loader for resumes list page.
 */

import { ResumeCardLoader } from '@/components/ui/loading'

export default function ResumesLoading() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mb-2"></div>
        <div className="h-4 w-64 bg-gray-200 rounded animate-pulse"></div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <ResumeCardLoader />
        <ResumeCardLoader />
        <ResumeCardLoader />
      </div>
    </div>
  )
}
