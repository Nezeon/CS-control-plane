import { ArrowUp, ArrowDown } from 'lucide-react'
import AnimatedCounter from './AnimatedCounter'
import { cn } from '../../utils/cn'
import { formatPercentChange } from '../../utils/formatters'

export default function MetricCard({ value = 0, label = '', trend, suffix = '', icon: Icon, className }) {
  const trendValue = trend != null ? formatPercentChange(trend) : null
  const trendPositive = trend != null && trend >= 0

  return (
    <div
      data-testid={`metric-card-${label}`}
      className={cn('card p-5 flex flex-col gap-1', className)}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-text-muted uppercase tracking-wide">
          {label}
        </span>
        {Icon && <Icon className="w-4 h-4 text-text-ghost" />}
      </div>

      <div className="flex items-end gap-2 mt-1">
        <AnimatedCounter value={value} suffix={suffix} className="text-2xl" />
        {trendValue && (
          <span
            className={cn(
              'inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs font-medium mb-0.5',
              trendPositive
                ? 'text-status-success bg-status-success/10'
                : 'text-status-danger bg-status-danger/10'
            )}
          >
            {trendPositive ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
            {trendValue}
          </span>
        )}
      </div>
    </div>
  )
}
