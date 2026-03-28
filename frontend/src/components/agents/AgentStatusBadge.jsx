const STATUS_STYLES = {
  running: {
    bg: 'color-mix(in srgb, var(--primary) 15%, transparent)',
    text: 'var(--primary)',
    dot: 'var(--primary)',
    pulse: true,
  },
  idle: {
    bg: 'var(--bg-hover)',
    text: 'var(--text-muted)',
    dot: 'var(--text-muted)',
    pulse: false,
  },
  error: {
    bg: 'color-mix(in srgb, var(--status-danger) 15%, transparent)',
    text: 'var(--status-danger)',
    dot: 'var(--status-danger)',
    pulse: false,
  },
  pending: {
    bg: 'color-mix(in srgb, var(--status-warning) 15%, transparent)',
    text: 'var(--status-warning)',
    dot: 'var(--status-warning)',
    pulse: true,
  },
  inactive: {
    bg: 'var(--bg-hover)',
    text: 'var(--text-ghost)',
    dot: 'var(--text-ghost)',
    pulse: false,
  },
}

export default function AgentStatusBadge({ status = 'idle' }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.idle

  return (
    <span
      className="inline-flex items-center gap-1.5 text-[11px] font-medium px-2 py-0.5 rounded-full"
      style={{ background: s.bg, color: s.text }}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${s.pulse ? 'animate-pulse-subtle' : ''}`}
        style={{ background: s.dot }}
      />
      {status === 'inactive' ? 'not configured' : status}
    </span>
  )
}
