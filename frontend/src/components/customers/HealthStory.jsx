import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import GlassCard from '../shared/GlassCard'

const EMPTY_ARRAY = []

function formatDate(d) {
  if (!d) return ''
  const date = new Date(d)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function getFactorColor(score) {
  if (score >= 70) return 'bg-status-success'
  if (score >= 40) return 'bg-status-warning'
  return 'bg-status-danger'
}

export default function HealthStory({ healthHistory = EMPTY_ARRAY, customer }) {
  const chartData = (healthHistory || []).map((h) => ({
    date: formatDate(h.recorded_at || h.date),
    score: h.score ?? h.health_score ?? 0,
  }))

  const factors = customer?.health_factors || []

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Health trend chart */}
      <GlassCard className="lg:col-span-2">
        <h3 className="text-sm font-medium text-text-primary mb-3">Health Trend</h3>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
              <defs>
                <linearGradient id="healthGradViolet" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#7C5CFC" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#7C5CFC" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: '#5C5C72', fontFamily: '"JetBrains Mono"' }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 11, fill: '#5C5C72', fontFamily: '"JetBrains Mono"' }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: '#12131A',
                  border: '1px solid #222438',
                  borderRadius: 12,
                  fontSize: 12,
                  fontFamily: '"JetBrains Mono"',
                }}
                labelStyle={{ color: '#8F8FA3' }}
                itemStyle={{ color: '#EDEDF0' }}
              />
              <Area
                type="monotone"
                dataKey="score"
                stroke="#7C5CFC"
                strokeWidth={2}
                fill="url(#healthGradViolet)"
                dot={false}
                activeDot={{ r: 4, fill: '#7C5CFC', stroke: '#050507', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-xs text-text-ghost py-16 text-center">No health history available</p>
        )}
      </GlassCard>

      {/* Health factors */}
      <GlassCard>
        <h3 className="text-sm font-medium text-text-primary mb-3">Health Factors</h3>
        {factors.length > 0 ? (
          <div className="space-y-3">
            {factors.map((f) => (
              <div key={f.name || f.label}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-text-muted">{f.name || f.label}</span>
                  <span className="text-xs font-mono text-text-primary tabular-nums">{f.score ?? f.value}</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-bg-active">
                  <div
                    className={`h-full rounded-full ${getFactorColor(f.score ?? f.value)} transition-all`}
                    style={{ width: `${Math.min(100, f.score ?? f.value ?? 0)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-text-ghost py-8 text-center">No factors available</p>
        )}
      </GlassCard>
    </div>
  )
}
