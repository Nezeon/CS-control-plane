import { useState } from 'react'
import { motion } from 'framer-motion'
import { Bot } from 'lucide-react'
import AgentStatusBadge from './AgentStatusBadge'
import { formatRelativeTime } from '../../utils/formatters'

const SOURCE_COLORS = {
  Jira: { bg: 'var(--chip-bg, rgba(59,158,255,0.1))', text: 'var(--sky)' },
  Fathom: { bg: 'var(--chip-bg, rgba(24,199,182,0.1))', text: 'var(--primary)' },
  HubSpot: { bg: 'var(--chip-bg, rgba(245,158,11,0.1))', text: 'var(--status-warning)' },
  Slack: { bg: 'var(--chip-bg, rgba(16,185,129,0.1))', text: 'var(--status-success)' },
  Cron: { bg: 'var(--bg-hover)', text: 'var(--text-muted)' },
}

export default function AgentCard({ agent }) {
  const { name, status, lastRun, description, sources = [], successRate } = agent
  const [hovered, setHovered] = useState(false)

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="rounded-lg p-4 flex flex-col gap-3 cursor-default transition-all duration-150"
      style={{
        background: 'var(--card-bg)',
        border: `1px solid ${hovered ? 'var(--primary)' : 'var(--border)'}`,
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-md flex items-center justify-center"
            style={{ background: 'var(--chip-bg, rgba(24,199,182,0.1))' }}
          >
            <Bot size={16} style={{ color: 'var(--primary)' }} />
          </div>
          <div>
            <h3 className="text-sm font-medium leading-tight" style={{ color: 'var(--text-primary)' }}>
              {name}
            </h3>
          </div>
        </div>
        <AgentStatusBadge status={status} />
      </div>

      {/* Description */}
      <p className="text-xs leading-relaxed line-clamp-2" style={{ color: 'var(--text-secondary)' }}>
        {description}
      </p>

      {/* Source tags */}
      {sources.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {sources.map(src => {
            const sc = SOURCE_COLORS[src] || SOURCE_COLORS.Cron
            return (
              <span
                key={src}
                className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                style={{ background: sc.bg, color: sc.text }}
              >
                {src}
              </span>
            )
          })}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-1 border-t" style={{ borderColor: 'var(--border)' }}>
        <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
          Last run: {lastRun ? formatRelativeTime(lastRun) : 'Never'}
        </span>
        {successRate != null && (
          <div className="flex items-center gap-2">
            <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-hover)' }}>
              <div
                className="h-full rounded-full"
                style={{
                  width: `${successRate}%`,
                  background: successRate >= 90 ? 'var(--status-success)' : successRate >= 70 ? 'var(--status-warning)' : 'var(--status-danger)',
                }}
              />
            </div>
            <span className="text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>
              {successRate}%
            </span>
          </div>
        )}
      </div>
    </motion.div>
  )
}
