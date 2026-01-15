import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils/cn"

interface LoadingStateProps {
  rows?: number
  className?: string
}

export function LoadingState({ rows = 3, className }: LoadingStateProps) {
  return (
    <div className={cn("space-y-4", className)}>
      <Skeleton className="h-8 w-40" />
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    </div>
  )
}

