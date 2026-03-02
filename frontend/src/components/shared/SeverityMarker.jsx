import { cn } from '../../utils/cn'
import { getSeverityColor } from '../../utils/formatters'

const severityLabels = {
  P1: 'Critical',
  P2: 'High',
  P3: 'Medium',
  P4: 'Low',
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
}

export default function SeverityMarker({ severity = 'P4', variant = 'badge' }) {
  const color = getSeverityColor(severity)
  const label = severityLabels[severity] || severity

  if (variant === 'line') {
    return (
      <div
        data-testid="severity-marker"
        className="absolute left-0 top-0 h-full w-[3px] rounded-r"
        style={{ backgroundColor: color }}
      />
    )
  }

  return (
    <span
      data-testid="severity-marker"
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded font-mono text-xxs font-medium uppercase tracking-wide',
      )}
      style={{
        color,
        backgroundColor: `${color}14`,
      }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  )
}
