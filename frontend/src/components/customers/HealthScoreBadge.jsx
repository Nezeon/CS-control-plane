export default function HealthScoreBadge({ score }) {
  if (score == null) {
    return (
      <span
        className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full"
        style={{ background: 'var(--bg-hover)', color: 'var(--text-muted)' }}
      >
        —
      </span>
    )
  }

  let bg, text
  if (score >= 80) {
    bg = 'var(--status-success)'
    text = 'var(--status-success)'
  } else if (score >= 50) {
    bg = 'var(--status-warning)'
    text = 'var(--status-warning)'
  } else {
    bg = 'var(--status-danger)'
    text = 'var(--status-danger)'
  }

  return (
    <span
      className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full"
      style={{ background: `color-mix(in srgb, ${bg} 15%, transparent)`, color: text }}
    >
      {score}
    </span>
  )
}
