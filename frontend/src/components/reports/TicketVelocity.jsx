import { useMemo, useCallback, memo } from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import useReportStore from '../../stores/reportStore'
import LoadingSkeleton from '../shared/LoadingSkeleton'
import { SEVERITY_COLORS } from '../../utils/chartHelpers'

const SEVERITY_ORDER = ['P4', 'P3', 'P2', 'P1']

function VelocityTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const total = payload.reduce((s, p) => s + (p.value || 0), 0)

  return (
    <div className="bg-bg-elevated rounded-lg px-3 py-2 border border-border text-xs">
      <div className="text-text-ghost font-mono mb-1.5">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }} />
            <span className="text-text-ghost font-mono">{p.dataKey}</span>
          </span>
          <span className="text-text-primary font-mono font-semibold">{p.value}</span>
        </div>
      ))}
      <div className="flex items-center justify-between gap-4 mt-1 pt-1 border-t border-border">
        <span className="text-text-ghost font-mono">Total</span>
        <span className="text-accent font-mono font-semibold">{total}</span>
      </div>
    </div>
  )
}

export default memo(function TicketVelocity({ data = [], isLoading }) {
  const crossFilter = useReportStore((s) => s.crossFilter)
  const setCrossFilter = useReportStore((s) => s.setCrossFilter)
  const clearCrossFilter = useReportStore((s) => s.clearCrossFilter)

  const chartData = useMemo(() => {
    return data.map((d) => ({
      week: d.week,
      P1: d.by_severity?.P1 ?? d.P1 ?? 0,
      P2: d.by_severity?.P2 ?? d.P2 ?? 0,
      P3: d.by_severity?.P3 ?? d.P3 ?? 0,
      P4: d.by_severity?.P4 ?? d.P4 ?? 0,
    }))
  }, [data])

  const getLayerOpacity = useCallback(
    (severity) => {
      if (!crossFilter) return 0.7
      if (crossFilter.source === 'velocity') return 0.7
      if (crossFilter.type === 'severity') {
        return crossFilter.value === severity ? 0.8 : 0.12
      }
      return 0.7
    },
    [crossFilter]
  )

  const handleClick = useCallback(
    (e) => {
      if (!e?.activePayload?.length) {
        clearCrossFilter()
        return
      }
      const topPayload = e.activePayload.reduce((best, p) =>
        (p.value > (best?.value || 0)) ? p : best, null
      )
      if (topPayload) {
        setCrossFilter({
          type: 'severity',
          value: topPayload.dataKey,
          source: 'velocity',
        })
      }
    },
    [setCrossFilter, clearCrossFilter]
  )

  if (isLoading) {
    return (
      <div className="card p-4 h-[280px]" data-testid="ticket-velocity">
        <LoadingSkeleton variant="rect" width="100%" height="240px" />
      </div>
    )
  }

  if (!chartData.length) {
    return (
      <div className="card p-4 h-[280px] flex flex-col items-center justify-center" data-testid="ticket-velocity">
        <div className="text-text-ghost font-mono text-sm mb-1">No ticket data available</div>
        <div className="text-text-ghost/40 font-mono text-[10px]">Ticket velocity will appear here</div>
      </div>
    )
  }

  return (
    <div className="card p-4" data-testid="ticket-velocity" role="img" aria-label="Ticket velocity stacked area chart by severity" tabIndex={0} onKeyDown={(e) => { if (e.key === 'Escape') clearCrossFilter() }}>
      <h3 className="text-xs text-text-primary font-semibold uppercase tracking-wider mb-3">
        Ticket Velocity
      </h3>

      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -20 }} onClick={handleClick}>
          <defs>
            {SEVERITY_ORDER.map((sev) => (
              <linearGradient key={sev} id={`vel-grad-${sev}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={SEVERITY_COLORS[sev]} stopOpacity={0.4} />
                <stop offset="95%" stopColor={SEVERITY_COLORS[sev]} stopOpacity={0.02} />
              </linearGradient>
            ))}
          </defs>

          <XAxis
            dataKey="week"
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#52525B', fontSize: 10, fontFamily: '"JetBrains Mono"' }}
            interval="preserveStartEnd"
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#52525B', fontSize: 10, fontFamily: '"JetBrains Mono"' }}
          />

          <Tooltip
            content={<VelocityTooltip />}
            cursor={{ stroke: 'rgba(63,63,70,0.2)', strokeWidth: 1 }}
          />

          {SEVERITY_ORDER.map((sev) => (
            <Area
              key={sev}
              type="monotone"
              dataKey={sev}
              stackId="severity"
              stroke={SEVERITY_COLORS[sev]}
              strokeWidth={1.5}
              fill={`url(#vel-grad-${sev})`}
              fillOpacity={getLayerOpacity(sev)}
              strokeOpacity={getLayerOpacity(sev) > 0.3 ? 1 : 0.3}
              dot={false}
              animationDuration={1500}
              animationEasing="ease-out"
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
})
