import { useMemo, useState, useCallback, memo } from 'react'
import * as d3 from 'd3'
import { motion } from 'framer-motion'
import useReportStore from '../../stores/reportStore'
import LoadingSkeleton from '../shared/LoadingSkeleton'
import { healthColorScale, getCrossFilterOpacity } from '../../utils/chartHelpers'
import { formatDate } from '../../utils/formatters'

const CELL = 14
const GAP = 2
const STEP = CELL + GAP
const LABEL_W = 90
const HEADER_H = 8
const BOTTOM_H = 20

function HeatmapTooltip({ cell, x, y }) {
  if (!cell) return null
  return (
    <div
      className="fixed z-50 bg-bg-elevated rounded-lg px-3 py-2 border border-border text-xs pointer-events-none"
      style={{ left: x + 12, top: y - 40 }}
    >
      <div className="text-text-primary font-semibold">{cell.customer}</div>
      <div className="text-text-ghost font-mono mt-0.5">{formatDate(cell.date)}</div>
      <div className="font-mono mt-0.5">
        Score: <span style={{ color: healthColorScale(cell.score) }}>{cell.score ?? '—'}</span>
      </div>
    </div>
  )
}

export default memo(function HealthHeatmap({ data = [], isLoading }) {
  const crossFilter = useReportStore((s) => s.crossFilter)
  const setCrossFilter = useReportStore((s) => s.setCrossFilter)
  const clearCrossFilter = useReportStore((s) => s.clearCrossFilter)
  const [tooltip, setTooltip] = useState(null)

  const { customers, dates, matrix, svgW, svgH } = useMemo(() => {
    if (!data.length) return { customers: [], dates: [], matrix: new Map(), svgW: 0, svgH: 0 }

    const custSet = new Map()
    const dateSet = new Set()
    data.forEach((d) => {
      const name = d.customer_name || d.customer_id || 'Unknown'
      if (!custSet.has(name)) custSet.set(name, d.customer_id || name)
      dateSet.add(d.date)
    })

    const customers = Array.from(custSet.keys()).slice(0, 12)
    const dates = Array.from(dateSet).sort().slice(-30)

    const matrix = new Map()
    data.forEach((d) => {
      const name = d.customer_name || d.customer_id
      matrix.set(`${name}|${d.date}`, d.score ?? d.avg_score ?? null)
    })

    const svgW = LABEL_W + dates.length * STEP + 10
    const svgH = HEADER_H + customers.length * STEP + BOTTOM_H

    return { customers, dates, matrix, svgW, svgH }
  }, [data])

  const handleCellHover = useCallback((e, customer, date, score) => {
    setTooltip({ customer, date, score, x: e.clientX, y: e.clientY })
  }, [])

  const handleCellLeave = useCallback(() => setTooltip(null), [])

  const handleRowClick = useCallback((customer) => {
    setCrossFilter({ type: 'customer', value: customer, source: 'heatmap' })
  }, [setCrossFilter])

  const handleCellClick = useCallback((date) => {
    setCrossFilter({ type: 'date', value: date, source: 'heatmap' })
  }, [setCrossFilter])

  if (isLoading) {
    return (
      <div className="card p-4 h-[280px]" data-testid="health-heatmap">
        <LoadingSkeleton variant="rect" width="100%" height="240px" />
      </div>
    )
  }

  if (!data.length) {
    return (
      <div className="card p-4 h-[280px] flex flex-col items-center justify-center" data-testid="health-heatmap">
        <div className="text-text-ghost font-mono text-sm mb-1">No health data available</div>
        <div className="text-text-ghost/40 font-mono text-[10px]">Health trends will appear here</div>
      </div>
    )
  }

  return (
    <div
      className="card p-4"
      data-testid="health-heatmap"
      role="img"
      aria-label="Health heatmap showing customer health scores over 30 days"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Escape') clearCrossFilter() }}
    >
      <h3 className="text-xs text-text-primary font-semibold uppercase tracking-wider mb-3">
        Health Heatmap
      </h3>

      <div className="overflow-x-auto scrollbar-thin">
        <svg
          width={svgW}
          height={svgH}
          viewBox={`0 0 ${svgW} ${svgH}`}
          className="block"
          onClick={(e) => { if (e.target.tagName === 'svg') clearCrossFilter() }}
        >
          {customers.map((customer, row) => {
            const rowOpacity = getCrossFilterOpacity(crossFilter, { customer_name: customer }, 'heatmap')
            return (
              <text
                key={`label-${row}`}
                x={LABEL_W - 6}
                y={HEADER_H + row * STEP + CELL / 2 + 1}
                textAnchor="end"
                dominantBaseline="central"
                className="cursor-pointer"
                style={{
                  fontFamily: '"JetBrains Mono"',
                  fontSize: 10,
                  fill: crossFilter?.type === 'customer' && crossFilter.value === customer
                    ? '#6366F1' : '#71717A',
                  opacity: rowOpacity,
                  transition: 'opacity 0.3s, fill 0.3s',
                }}
                onClick={() => handleRowClick(customer)}
              >
                {customer.length > 12 ? customer.slice(0, 11) + '…' : customer}
              </text>
            )
          })}

          {dates.map((date, col) => {
            if (col % 5 !== 0) return null
            const d = new Date(date)
            return (
              <text
                key={`date-${col}`}
                x={LABEL_W + col * STEP + CELL / 2}
                y={HEADER_H + customers.length * STEP + 12}
                textAnchor="middle"
                style={{
                  fontFamily: '"JetBrains Mono"',
                  fontSize: 9,
                  fill: '#52525B',
                }}
              >
                {`${d.getMonth() + 1}/${d.getDate()}`}
              </text>
            )
          })}

          {customers.map((customer, row) =>
            dates.map((date, col) => {
              const score = matrix.get(`${customer}|${date}`)
              const fill = score != null ? healthColorScale(score) : 'rgba(39,39,42,0.4)'

              const cellOpacity = getCrossFilterOpacity(
                crossFilter,
                { customer_name: customer, date },
                'heatmap'
              )

              return (
                <motion.rect
                  key={`${row}-${col}`}
                  x={LABEL_W + col * STEP}
                  y={HEADER_H + row * STEP}
                  width={CELL}
                  height={CELL}
                  rx={2}
                  fill={fill}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: cellOpacity }}
                  transition={{ duration: 0.3, delay: (row * 0.01 + col * 0.005) }}
                  className="cursor-pointer"
                  style={{ transition: 'opacity 0.3s' }}
                  onMouseEnter={(e) => handleCellHover(e, customer, date, score)}
                  onMouseLeave={handleCellLeave}
                  onClick={() => handleCellClick(date)}
                />
              )
            })
          )}
        </svg>
      </div>

      {tooltip && <HeatmapTooltip cell={tooltip} x={tooltip.x} y={tooltip.y} />}
    </div>
  )
})
