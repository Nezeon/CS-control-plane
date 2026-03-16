import { cn } from '../../utils/cn'

const statusConfig = {
  active:       { dot: 'bg-status-success',  text: 'text-status-success',  glow: false, pulse: false },
  open:         { dot: 'bg-status-success',  text: 'text-status-success',  glow: false, pulse: false },
  running:      { dot: 'bg-status-success',  text: 'text-status-success',  glow: false, pulse: false },
  idle:         { dot: 'bg-text-ghost',      text: 'text-text-ghost',      glow: false, pulse: false },
  pending:      { dot: 'bg-text-ghost',      text: 'text-text-ghost',      glow: false, pulse: false },
  queued:       { dot: 'bg-text-ghost',      text: 'text-text-ghost',      glow: false, pulse: false },
  completed:    { dot: 'bg-teal',            text: 'text-teal',            glow: false, pulse: false },
  resolved:     { dot: 'bg-teal',            text: 'text-teal',            glow: false, pulse: false },
  failed:       { dot: 'bg-status-danger',   text: 'text-status-danger',   glow: false, pulse: false },
  error:        { dot: 'bg-status-danger',   text: 'text-status-danger',   glow: false, pulse: false },
  critical:     { dot: 'bg-status-danger',   text: 'text-status-danger',   glow: true,  pulse: false },
  acknowledged: { dot: 'bg-status-warning',  text: 'text-status-warning',  glow: false, pulse: false },
  processing:   { dot: 'bg-accent',          text: 'text-accent',          glow: false, pulse: true  },
}

const fallback = { dot: 'bg-text-ghost', text: 'text-text-muted', glow: false, pulse: false }

const sizeClasses = {
  sm: 'text-xxs px-2 py-0.5 gap-1.5',
  md: 'text-xs px-2.5 py-1 gap-2',
}

export default function StatusPill({ status = 'idle', size = 'sm', className }) {
  const config = statusConfig[status] || fallback
  const label = status.charAt(0).toUpperCase() + status.slice(1)

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        sizeClasses[size] || sizeClasses.sm,
        config.text,
        className
      )}
    >
      <span
        className={cn(
          'h-1.5 w-1.5 rounded-full flex-shrink-0',
          config.dot,
          config.glow && 'shadow-[0_0_6px_rgba(255,92,92,0.6)]',
          config.pulse && 'animate-pulse-subtle'
        )}
      />
      {label}
    </span>
  )
}
