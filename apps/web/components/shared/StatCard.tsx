import { ReactNode } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils/cn"

interface StatCardProps {
  label: string
  value: string | number
  icon?: ReactNode
  trend?: string
  tone?: "default" | "success" | "warn" | "error"
  className?: string
}

const toneRing: Record<NonNullable<StatCardProps["tone"]>, string> = {
  default: "ring-primary/40",
  success: "ring-emerald-400/40",
  warn: "ring-amber-400/40",
  error: "ring-rose-400/40",
}

export function StatCard({
  label,
  value,
  icon,
  trend,
  tone = "default",
  className,
}: StatCardProps) {
  return (
    <Card
      className={cn(
        "relative overflow-hidden border-soft-border/70 bg-elevated/80 shadow-soft backdrop-blur",
        "ring-1 ring-inset ring-border/40 hover:ring-2 hover:ring-primary/40 transition-all",
        className,
      )}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
        {icon && (
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full border bg-background/80 text-primary",
              "shadow-inset",
            )}
          >
            {icon}
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between gap-3">
          <div className="text-2xl font-semibold tracking-tight">
            {value}
          </div>
          {trend && (
            <div className="rounded-full bg-primary/6 px-3 py-1 text-xs font-medium text-primary">
              {trend}
            </div>
          )}
        </div>
      </CardContent>
      <div
        className={cn(
          "pointer-events-none absolute inset-px rounded-[calc(var(--radius)-2px)] border border-white/5",
          "shadow-glass",
          toneRing[tone],
        )}
      />
    </Card>
  )
}

