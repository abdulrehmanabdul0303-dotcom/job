import { ReactNode } from "react"
import { cn } from "@/lib/utils/cn"

interface PageHeaderProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  className?: string
}

export function PageHeader({ title, subtitle, actions, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        "mb-6 flex flex-col gap-3 border-b border-soft-border/60 pb-4 md:mb-8 md:flex-row md:items-center md:justify-between",
        className,
      )}
    >
      <div>
        <h1 className="text-h1 font-semibold tracking-tight">{title}</h1>
        {subtitle && (
          <p className="mt-1 max-w-2xl text-body text-muted-foreground">
            {subtitle}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex flex-wrap items-center gap-2">
          {actions}
        </div>
      )}
    </div>
  )
}

