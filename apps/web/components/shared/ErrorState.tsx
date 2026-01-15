import { ReactNode } from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils/cn"

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
  footer?: ReactNode
  className?: string
}

export function ErrorState({
  title = "Something went wrong",
  message = "We couldn’t load this section. Please try again.",
  onRetry,
  footer,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-destructive/20 bg-destructive/5 px-6 py-8 text-center shadow-soft",
        className,
      )}
    >
      <div className="mb-3 text-sm font-semibold text-destructive">
        {title}
      </div>
      <p className="max-w-md text-sm text-muted-foreground">
        {message}
      </p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="mt-4"
        >
          Retry
        </Button>
      )}
      {footer && <div className="mt-3 text-xs text-muted-foreground">{footer}</div>}
    </div>
  )
}

