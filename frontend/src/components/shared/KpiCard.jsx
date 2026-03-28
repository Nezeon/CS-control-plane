const COLORS = {
  accent: { bg: 'bg-[#18C7B6]/10', text: 'text-[#18C7B6]' },
  teal:   { bg: 'bg-[#00E5C4]/10',  text: 'text-[#00E5C4]' },
  sky:    { bg: 'bg-[#3B9EFF]/10',  text: 'text-[#3B9EFF]' },
}

export default function KpiCard({ label, value, trend, icon: Icon, color = 'accent' }) {
  const c = COLORS[color] || COLORS.accent

  return (
    <div className="glass-near p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between">
        {Icon && (
          <div className={`flex items-center justify-center w-9 h-9 rounded-lg ${c.bg}`}>
            <Icon size={18} className={c.text} />
          </div>
        )}
        {typeof trend === 'number' && trend !== 0 && (
          <span className={`text-xs font-mono ${trend > 0 ? 'text-[var(--status-success)]' : 'text-[var(--status-danger)]'}`}>
            {trend > 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>
      <span className="font-display text-2xl font-bold text-[var(--text-primary)]">{value}</span>
      <span className="font-mono text-[10px] uppercase tracking-wider text-[var(--text-muted)]">{label}</span>
    </div>
  )
}
