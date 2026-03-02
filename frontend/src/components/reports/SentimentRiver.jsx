import { useMemo, useState, useCallback, useRef, memo } from 'react'
import * as d3 from 'd3'
import { motion } from 'framer-motion'
import useReportStore from '../../stores/reportStore'
import LoadingSkeleton from '../shared/LoadingSkeleton'
import { SENTIMENT_COLORS, getCrossFilterOpacity } from '../../utils/chartHelpers'

const MARGIN = { top: 12, right: 16, bottom: 28, left: 16 }
const KEYS = ['positive', 'neutral', 'negative']
const KEY_LABELS = { positive: 'Positive', neutral: 'Neutral', negative: 'Negative' }

function RiverTooltip({ info, x, y }) {
  if (!info) return null
  return (
    <div
      className="fixed z-50 bg-bg-elevated rounded-lg px-3 py-2 border border-border text-xs pointer-events-none"
      style={{ left: x + 14, top: y - 50 }}
    >
      <div className="text-text-ghost font-mono mb-1.5">{info.date}</div>
      {KEYS.map((k) => (
        <div key={k} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: SENTIMENT_COLORS[k] }}
            />
            <span className="text-text-ghost font-mono">{KEY_LABELS[k]}</span>
          </span>
          <span className="text-text-primary font-mono font-semibold">
            {(info[k] ?? 0).toFixed(1)}
          </span>
        </div>
      ))}
    </div>
  )
}

export default memo(function SentimentRiver({ data = [], isLoading }) {
  const crossFilter = useReportStore((s) => s.crossFilter)
  const setCrossFilter = useReportStore((s) => s.setCrossFilter)
  const clearCrossFilter = useReportStore((s) => s.clearCrossFilter)
  const [tooltip, setTooltip] = useState(null)
  const svgRef = useRef(null)

  const width = 560
  const height = 220
  const innerW = width - MARGIN.left - MARGIN.right
  const innerH = height - MARGIN.top - MARGIN.bottom

  const { stackedData, xScale, yScale, areaGen, dateLabels } = useMemo(() => {
    if (!data.length) return { stackedData: [], xScale: null, yScale: null, areaGen: null, dateLabels: [] }

    const stack = d3.stack()
      .keys(KEYS)
      .offset(d3.stackOffsetWiggle)
      .order(d3.stackOrderInsideOut)

    const stacked = stack(data)

    const xScale = d3.scaleLinear()
      .domain([0, data.length - 1])
      .range([0, innerW])

    const yMin = d3.min(stacked, (layer) => d3.min(layer, (d) => d[0]))
    const yMax = d3.max(stacked, (layer) => d3.max(layer, (d) => d[1]))
    const yScale = d3.scaleLinear()
      .domain([yMin, yMax])
      .range([innerH, 0])

    const areaGen = d3.area()
      .x((d, i) => xScale(i))
      .y0((d) => yScale(d[0]))
      .y1((d) => yScale(d[1]))
      .curve(d3.curveBasis)

    const dateLabels = data
      .map((d, i) => ({ date: d.date, i }))
      .filter((_, i) => i % 5 === 0)

    return { stackedData: stacked, xScale, yScale, areaGen, dateLabels }
  }, [data, innerW, innerH])

  const handleMouseMove = useCallback((e) => {
    if (!xScale || !data.length || !svgRef.current) return
    const svgRect = svgRef.current.getBoundingClientRect()
    const mouseX = e.clientX - svgRect.left - MARGIN.left
    const idx = Math.round(xScale.invert(mouseX))
    const clamped = Math.max(0, Math.min(data.length - 1, idx))
    const datum = data[clamped]
    if (datum) {
      setTooltip({
        date: datum.date,
        positive: datum.positive,
        neutral: datum.neutral,
        negative: datum.negative,
        x: e.clientX,
        y: e.clientY,
      })
    }
  }, [xScale, data])

  const handleMouseLeave = useCallback(() => setTooltip(null), [])

  const handleClick = useCallback((e) => {
    if (!xScale || !data.length || !svgRef.current) return
    const svgRect = svgRef.current.getBoundingClientRect()
    const mouseX = e.clientX - svgRect.left - MARGIN.left
    const idx = Math.round(xScale.invert(mouseX))
    const clamped = Math.max(0, Math.min(data.length - 1, idx))
    const datum = data[clamped]
    if (datum?.date) {
      setCrossFilter({ type: 'date', value: datum.date, source: 'river' })
    }
  }, [xScale, data, setCrossFilter])

  const handleBgClick = useCallback((e) => {
    if (e.target.tagName === 'svg') clearCrossFilter()
  }, [clearCrossFilter])

  if (isLoading) {
    return (
      <div className="card p-4 h-[280px]" data-testid="sentiment-river">
        <LoadingSkeleton variant="rect" width="100%" height="240px" />
      </div>
    )
  }

  if (!data.length) {
    return (
      <div className="card p-4 h-[280px] flex flex-col items-center justify-center" data-testid="sentiment-river">
        <div className="text-text-ghost font-mono text-sm mb-1">No sentiment data available</div>
        <div className="text-text-ghost/40 font-mono text-[10px]">Sentiment streams will appear here</div>
      </div>
    )
  }

  return (
    <div className="card p-4" data-testid="sentiment-river" role="img" aria-label="Sentiment river stream graph showing positive, neutral, and negative sentiment over time" tabIndex={0} onKeyDown={(e) => { if (e.key === 'Escape') clearCrossFilter() }}>
      <h3 className="text-xs text-text-primary font-semibold uppercase tracking-wider mb-3">
        Sentiment River
      </h3>

      <div className="overflow-x-auto scrollbar-thin">
        <svg
          ref={svgRef}
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          className="block w-full"
          style={{ minWidth: 400 }}
          onClick={handleBgClick}
        >
          <defs>
            <clipPath id="river-clip">
              <motion.rect
                x={0}
                y={0}
                height={height}
                initial={{ width: 0 }}
                animate={{ width }}
                transition={{ duration: 2, ease: 'easeOut' }}
              />
            </clipPath>

            {KEYS.map((key) => (
              <linearGradient key={key} id={`river-grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={SENTIMENT_COLORS[key]} stopOpacity={0.5} />
                <stop offset="100%" stopColor={SENTIMENT_COLORS[key]} stopOpacity={0.15} />
              </linearGradient>
            ))}
          </defs>

          <g transform={`translate(${MARGIN.left},${MARGIN.top})`} clipPath="url(#river-clip)">
            {stackedData.map((layer, li) => {
              const key = KEYS[li]
              const pathD = areaGen(layer)
              const layerOpacity = getCrossFilterOpacity(
                crossFilter,
                { date: '__all__' },
                'river'
              )

              return (
                <motion.path
                  key={key}
                  d={pathD}
                  fill={`url(#river-grad-${key})`}
                  stroke={SENTIMENT_COLORS[key]}
                  strokeWidth={1}
                  strokeOpacity={0.6}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: layerOpacity * 0.85 }}
                  transition={{ duration: 0.5, delay: li * 0.15 }}
                  className="cursor-pointer"
                  onMouseMove={handleMouseMove}
                  onMouseLeave={handleMouseLeave}
                  onClick={handleClick}
                />
              )
            })}

            {crossFilter?.type === 'date' && crossFilter.source !== 'river' && xScale && (() => {
              const matchIdx = data.findIndex((d) => d.date === crossFilter.value)
              if (matchIdx < 0) return null
              const cx = xScale(matchIdx)
              return (
                <rect
                  x={cx - 2}
                  y={0}
                  width={4}
                  height={innerH}
                  fill="#6366F1"
                  opacity={0.3}
                  rx={2}
                />
              )
            })()}

            {dateLabels.map(({ date, i }) => {
              const x = xScale(i)
              const d = new Date(date)
              return (
                <text
                  key={`dl-${i}`}
                  x={x}
                  y={innerH + 16}
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
          </g>

          {KEYS.map((key, i) => (
            <g key={`legend-${key}`} transform={`translate(${width - 200 + i * 68}, 6)`}>
              <circle cx={4} cy={4} r={3} fill={SENTIMENT_COLORS[key]} />
              <text
                x={10}
                y={7}
                style={{
                  fontFamily: '"JetBrains Mono"',
                  fontSize: 8,
                  fill: '#52525B',
                }}
              >
                {KEY_LABELS[key]}
              </text>
            </g>
          ))}
        </svg>
      </div>

      {tooltip && <RiverTooltip info={tooltip} x={tooltip.x} y={tooltip.y} />}
    </div>
  )
})
