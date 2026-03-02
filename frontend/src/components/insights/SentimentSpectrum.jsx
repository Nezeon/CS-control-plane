import { useMemo } from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import LoadingSkeleton from '../shared/LoadingSkeleton'
import { formatDate } from '../../utils/formatters'

/* ─── Custom tooltip ─── */
function SpectrumTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const val = payload[0].value
  const color = val > 0.2 ? '#22C55E' : val < -0.2 ? '#EF4444' : '#71717A'

  return (
    <div className="bg-bg-elevated rounded-lg px-3 py-2 border border-border text-xs">
      <div className="text-text-ghost font-mono mb-1">{formatDate(label)}</div>
      <div className="font-semibold" style={{ color }}>
        {val > 0 ? '+' : ''}{val.toFixed(2)}
      </div>
    </div>
  )
}

export default function SentimentSpectrum({ data = [], isLoading = false, onPointClick }) {
  const chartData = useMemo(() => {
    return data.map((d) => ({
      date: d.date || d.day,
      score: typeof d.avg_sentiment_score === 'number'
        ? d.avg_sentiment_score
        : typeof d.score === 'number'
          ? d.score
          : 0,
    }))
  }, [data])

  if (isLoading) {
    return (
      <div className="card p-4 h-[200px]">
        <LoadingSkeleton variant="rect" width="100%" height="160px" />
      </div>
    )
  }

  if (chartData.length === 0) {
    return (
      <div className="card p-4 h-[200px] flex items-center justify-center">
        <span className="text-text-ghost font-mono text-sm">No sentiment data available</span>
      </div>
    )
  }

  return (
    <div className="card p-4" data-testid="sentiment-spectrum">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm text-text-primary font-semibold">
          Sentiment Spectrum
        </h3>
        <div className="flex items-center gap-4 text-[10px] font-mono text-text-ghost">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-status-success" /> Positive
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-text-muted" /> Neutral
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-status-danger" /> Negative
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={180}>
        <AreaChart
          data={chartData}
          margin={{ top: 8, right: 8, bottom: 0, left: -20 }}
          onClick={(e) => {
            if (e?.activePayload?.[0]?.payload?.date && onPointClick) {
              onPointClick(e.activePayload[0].payload.date)
            }
          }}
        >
          <defs>
            <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#22C55E" stopOpacity={0.4} />
              <stop offset="45%" stopColor="#22C55E" stopOpacity={0.05} />
              <stop offset="55%" stopColor="#EF4444" stopOpacity={0.05} />
              <stop offset="100%" stopColor="#EF4444" stopOpacity={0.4} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="date"
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#52525B', fontSize: 10, fontFamily: '"JetBrains Mono"' }}
            tickFormatter={(d) => {
              const date = new Date(d)
              return `${date.getMonth() + 1}/${date.getDate()}`
            }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[-1, 1]}
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#52525B', fontSize: 10, fontFamily: '"JetBrains Mono"' }}
            tickFormatter={(v) => v.toFixed(1)}
            ticks={[-1, -0.5, 0, 0.5, 1]}
          />
          <Tooltip content={<SpectrumTooltip />} cursor={{ stroke: 'rgba(63,63,70,0.3)' }} />
          <Area
            type="monotone"
            dataKey={() => 0}
            stroke="rgba(63,63,70,0.3)"
            strokeWidth={1}
            strokeDasharray="4 4"
            fill="none"
            dot={false}
            isAnimationActive={false}
          />
          <Area
            type="monotone"
            dataKey="score"
            stroke="#6366F1"
            strokeWidth={2}
            fill="url(#sentimentGradient)"
            dot={false}
            activeDot={{
              r: 5,
              stroke: '#6366F1',
              strokeWidth: 2,
              fill: '#09090B',
            }}
            animationDuration={2000}
            animationEasing="ease-out"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
