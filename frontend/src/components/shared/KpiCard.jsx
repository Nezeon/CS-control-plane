import { cn } from '../../utils/cn'
import AnimatedCounter from './AnimatedCounter'
import SparkLine from './SparkLine'

const colorMap = {
  accent: { bg: 'bg-accent/10', text: 'text-accent', spark: '#7C5CFC' },
  teal:   { bg: 'bg-teal/10',   text: 'text-teal',   spark: '#00E5C4' },
  sky:    { bg: 'bg-sky/10',    text: 'text-sky',    spark: '#3B9EFF' },
}

export default function KpiCard({ label, value, trend, icon: Icon, color = 'accent', sparkData, className }) {
  const palette = colorMap[color] || colorMap.accent
  const trendPositive = typeof trend === 'number' && trend > 0
  const trendNegative = typeof trend === 'number' && trend < 0

  return (
    <div className={cn('glass-near p-4 flex flex-col gap-3', className)}>
      {/* Header row: icon + trend */}
      <div className="flex items-start justify-between">
        {Icon && (
          <div className={cn('flex items-center justify-center w-9 h-9 rounded-lg', palette.bg)}>
            <Icon size={18} className={palette.text} />
          </div>
        )}
        {typeof trend === 'number' && trend !== 0 && (
          <span
            className={cn(
              'inline-flex items-center gap-0.5 text-xxs font-medium font-mono',
              trendPositive && 'text-status-success',
              trendNegative && 'text-status-danger'
            )}
          >
            <svg
              width="10"
              height="10"
              viewBox="0 0 10 10"
              fill="none"
              className={cn(trendNegative && 'rotate-180')}
            >
              <path d="M5 2L8 6H2L5 2Z" fill="currentColor" />
            </svg>
            {Math.abs(trend)}%
          </span>
        )}
      </div>

      {/* Value */}
      <div>
        {typeof value === 'number' ? (
          <AnimatedCounter value={value} className="font-display text-2xl font-bold text-text-primary" />
        ) : (
          <span className="font-display text-2xl font-bold text-text-primary">{value}</span>
        )}
      </div>

      {/* Label */}
      <span className="font-mono text-xxs uppercase tracking-wider text-text-muted">
        {label}
      </span>

      {/* Sparkline */}
      {sparkData && sparkData.length >= 2 && (
        <div className="mt-auto pt-1">
          <SparkLine data={sparkData} width={120} height={24} color={palette.spark} />
        </div>
      )}
    </div>
  )
}
