import { ReactNode } from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils/cn"

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  actionLabel?: string
  onActionClick?: () => void
  secondaryAction?: ReactNode
  className?: string
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onActionClick,
  secondaryAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-2xl border border-dashed border-soft-border/80",
        "bg-orb-gradient/40 px-6 py-10 text-center shadow-soft",
        className,
      )}
    >
      {icon && (
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-background/70 text-primary shadow-soft">
          {icon}
        </div>
      )}
      <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
      {description && (
        <p className="mt-2 max-w-md text-sm text-muted-foreground">
          {description}
        </p>
      )}
      {(actionLabel || secondaryAction) && (
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          {actionLabel && onActionClick && (
            <Button onClick={onActionClick}>{actionLabel}</Button>
          )}
          {secondaryAction}
        </div>
      )}
    </div>
  )
}

