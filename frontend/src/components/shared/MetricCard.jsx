import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { ResponsiveContainer, LineChart, Line } from 'recharts'

export default function MetricCard({ title, value, delta, deltaType = 'neutral', icon: Icon, trend }) {
  const deltaColors = {
    positive: { bg: 'color-mix(in srgb, var(--status-success) 15%, transparent)', text: 'var(--status-success)' },
    negative: { bg: 'color-mix(in srgb, var(--status-danger) 15%, transparent)', text: 'var(--status-danger)' },
    neutral: { bg: 'var(--bg-hover)', text: 'var(--text-muted)' },
  }
  const dc = deltaColors[deltaType] || deltaColors.neutral
  const DeltaIcon = deltaType === 'positive' ? TrendingUp : deltaType === 'negative' ? TrendingDown : Minus

  const sparkData = trend ? trend.map((v, i) => ({ v, i })) : null

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="rounded-lg p-4 flex flex-col gap-3 cursor-default transition-colors duration-150"
      style={{
        background: 'var(--card-bg)',
        border: '1px solid var(--border)',
      }}
    >
      <div className="flex items-start justify-between">
        <span className="text-xs uppercase tracking-wider font-medium" style={{ color: 'var(--text-label, var(--text-muted))' }}>
          {title}
        </span>
        {Icon && (
          <div
            className="w-8 h-8 rounded-md flex items-center justify-center"
            style={{ background: 'color-mix(in srgb, var(--primary) 15%, transparent)' }}
          >
            <Icon size={16} style={{ color: 'var(--primary)' }} />
          </div>
        )}
      </div>

      <div className="flex items-end justify-between">
        <span className="text-[28px] font-light" style={{ color: 'var(--text-primary)' }}>
          {value}
        </span>
        {delta != null && (
          <span
            className="flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full"
            style={{ background: dc.bg, color: dc.text }}
          >
            <DeltaIcon size={12} />
            {delta}
          </span>
        )}
      </div>

      {sparkData && (
        <div className="h-8 -mx-1">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparkData}>
              <Line
                type="monotone"
                dataKey="v"
                stroke="#18C7B6"
                strokeWidth={1.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </motion.div>
  )
}
