const STYLES = {
  active: 'text-[var(--status-success)]', open: 'text-[var(--status-success)]',
  running: 'text-[var(--status-success)]', completed: 'text-[var(--teal)]',
  resolved: 'text-[var(--teal)]', closed: 'text-[var(--text-ghost)]',
  failed: 'text-[var(--status-danger)]', error: 'text-[var(--status-danger)]',
  critical: 'text-[var(--status-danger)]', high: 'text-[var(--status-danger)]',
  high_risk: 'text-[var(--status-danger)]',
  medium: 'text-[var(--status-warning)]', medium_risk: 'text-[var(--status-warning)]',
  acknowledged: 'text-[var(--status-warning)]', processing: 'text-[var(--accent)]',
  positive: 'text-[var(--status-success)]', negative: 'text-[var(--status-danger)]',
  neutral: 'text-[var(--text-muted)]', mixed: 'text-[var(--status-warning)]',
  healthy: 'text-[var(--status-success)]',
  P1: 'text-[var(--status-danger)]', P2: 'text-[var(--status-warning)]',
  P3: 'text-[var(--text-muted)]', P4: 'text-[var(--text-ghost)]',
}

const DOTS = {
  active: 'bg-[var(--status-success)]', open: 'bg-[var(--status-success)]',
  running: 'bg-[var(--status-success)]', completed: 'bg-[var(--teal)]',
  resolved: 'bg-[var(--teal)]', failed: 'bg-[var(--status-danger)]',
  critical: 'bg-[var(--status-danger)]', high_risk: 'bg-[var(--status-danger)]',
  healthy: 'bg-[var(--status-success)]', processing: 'bg-[var(--accent)]',
}

export default function StatusPill({ status = 'idle' }) {
  const label = (status || 'idle').replace(/_/g, ' ')
  const textCls = STYLES[status] || 'text-[var(--text-ghost)]'
  const dotCls = DOTS[status] || 'bg-[var(--text-ghost)]'

  return (
    <span className={`inline-flex items-center gap-1.5 text-[11px] font-medium ${textCls}`}>
      <span className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${dotCls}`} />
      {label.charAt(0).toUpperCase() + label.slice(1)}
    </span>
  )
}
