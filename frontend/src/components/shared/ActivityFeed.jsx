import { formatRelativeTime } from '../../utils/formatters'

const TYPE_COLORS = {
  info: 'var(--primary)',
  warning: 'var(--status-warning)',
  error: 'var(--status-danger)',
  success: 'var(--status-success)',
}

export default function ActivityFeed({ items = [] }) {
  return (
    <div
      className="rounded-lg overflow-hidden flex flex-col"
      style={{ background: 'var(--card-bg)', border: '1px solid var(--border)' }}
    >
      <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          Activity
        </span>
      </div>
      <div className="flex-1 overflow-y-auto max-h-[520px]">
        {items.length === 0 && (
          <div className="p-4 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
            No recent activity
          </div>
        )}
        {items.map((item) => (
          <div
            key={item.id}
            className="flex gap-3 px-4 py-3 transition-colors duration-150 cursor-default"
            style={{ borderBottom: '1px solid var(--border)' }}
          >
            <div
              className="w-0.5 flex-shrink-0 rounded-full self-stretch"
              style={{ background: TYPE_COLORS[item.type] || TYPE_COLORS.info }}
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm leading-snug" style={{ color: 'var(--text-primary)' }}>
                {item.message}
              </p>
              <div className="flex items-center gap-2 mt-1">
                {item.agentName && (
                  <span
                    className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                    style={{
                      background: 'var(--chip-bg, rgba(24,199,182,0.1))',
                      color: 'var(--chip-text, var(--primary))',
                    }}
                  >
                    {item.agentName}
                  </span>
                )}
                <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                  {formatRelativeTime(item.timestamp)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
