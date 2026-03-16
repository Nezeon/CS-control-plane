import { useMemo, useState, useCallback, memo } from 'react'
import * as d3 from 'd3'
import { m } from 'framer-motion'
import useReportStore from '../../stores/reportStore'
import LoadingSkeleton from '../shared/LoadingSkeleton'
import { AGENT_LANE_MAP, getCrossFilterOpacity } from '../../utils/chartHelpers'
import { getLaneColor, formatNumber } from '../../utils/formatters'

const EMPTY_ARRAY = []

const SIZE = 300
const CENTER = SIZE / 2
const INNER_R = 42
const OUTER_R = 138
const RING_W = 8
const RING_GAP = 3

function ThroughputTooltip({ info, x, y }) {
  if (!info) return null
  return (
    <div
      className="fixed z-50 bg-bg-elevated rounded-lg px-3 py-2 border border-border text-xs pointer-events-none"
      style={{ left: x + 14, top: y - 50 }}
    >
      <div className="text-text-primary font-semibold">{info.agent}</div>
      <div className="flex items-center gap-2 mt-1">
        <span
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: info.color }}
        />
        <span className="text-text-ghost font-mono">{info.lane}</span>
      </div>
      <div className="mt-1 font-mono">
        Tasks: <span className="text-text-primary font-semibold">{info.tasks}</span>
      </div>
      {info.avgDuration != null && (
        <div className="font-mono">
          Avg: <span className="text-text-primary font-semibold">
            {info.avgDuration < 1000
              ? `${info.avgDuration}ms`
              : `${(info.avgDuration / 1000).toFixed(1)}s`}
          </span>
        </div>
      )}
    </div>
  )
}

export default memo(function AgentThroughput({ data = EMPTY_ARRAY, isLoading }) {
  const crossFilter = useReportStore((s) => s.crossFilter)
  const setCrossFilter = useReportStore((s) => s.setCrossFilter)
  const clearCrossFilter = useReportStore((s) => s.clearCrossFilter)
  const [tooltip, setTooltip] = useState(null)

  const { rings, totalTasks } = useMemo(() => {
    if (!data.length) return { rings: [], totalTasks: 0 }

    const sorted = [...data]
      .sort((a, b) => (b.tasks_completed ?? 0) - (a.tasks_completed ?? 0))
      .slice(0, 10)

    const maxTasks = d3.max(sorted, (d) => d.tasks_completed ?? 0) || 1
    const totalTasks = d3.sum(sorted, (d) => d.tasks_completed ?? 0)

    const ringCount = sorted.length
    const availableRadius = OUTER_R - INNER_R
    const actualRingW = Math.min(RING_W, (availableRadius - (ringCount - 1) * RING_GAP) / ringCount)

    const rings = sorted.map((agent, i) => {
      const innerRadius = INNER_R + i * (actualRingW + RING_GAP)
      const outerRadius = innerRadius + actualRingW
      const proportion = (agent.tasks_completed ?? 0) / maxTasks
      const endAngle = proportion * Math.PI * 2

      const agentKey = agent.agent?.toLowerCase().replace(/\s+/g, '_')
      const lane = agent.lane || AGENT_LANE_MAP[agentKey] || 'control'
      const color = getLaneColor(lane)

      const arcGen = d3.arc()
        .innerRadius(innerRadius)
        .outerRadius(outerRadius)
        .startAngle(0)
        .cornerRadius(4)

      const bgPath = arcGen({ endAngle: Math.PI * 2 })
      const fgPath = arcGen({ endAngle })

      return {
        agent: agent.agent || agentKey || 'Unknown',
        tasks: agent.tasks_completed ?? 0,
        avgDuration: agent.avg_duration_ms ?? null,
        lane,
        color,
        innerRadius,
        outerRadius,
        endAngle,
        bgPath,
        fgPath,
        index: i,
      }
    })

    return { rings, totalTasks }
  }, [data])

  const handleRingHover = useCallback((e, ring) => {
    setTooltip({
      agent: ring.agent,
      lane: ring.lane,
      color: ring.color,
      tasks: ring.tasks,
      avgDuration: ring.avgDuration,
      x: e.clientX,
      y: e.clientY,
    })
  }, [])

  const handleRingLeave = useCallback(() => setTooltip(null), [])

  const handleRingClick = useCallback((ring) => {
    setCrossFilter({ type: 'agent', value: ring.agent, source: 'throughput' })
  }, [setCrossFilter])

  if (isLoading) {
    return (
      <div className="card p-4 h-[280px]" data-testid="agent-throughput">
        <LoadingSkeleton variant="rect" width="100%" height="240px" />
      </div>
    )
  }

  if (!data.length) {
    return (
      <div className="card p-4 h-[280px] flex flex-col items-center justify-center" data-testid="agent-throughput">
        <div className="text-text-ghost font-mono text-sm mb-1">No agent data available</div>
        <div className="text-text-ghost/40 font-mono text-[10px]">Agent throughput will appear here</div>
      </div>
    )
  }

  return (
    <div className="card p-4" data-testid="agent-throughput" role="img" aria-label="Agent throughput radial bar chart showing tasks completed per agent" tabIndex={0} onKeyDown={(e) => { if (e.key === 'Escape') clearCrossFilter() }}>
      <h3 className="text-xs text-text-primary font-semibold uppercase tracking-wider mb-3">
        Agent Throughput
      </h3>

      <div className="flex justify-center">
        <svg
          width={SIZE}
          height={SIZE}
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="block"
          onClick={(e) => { if (e.target.tagName === 'svg') clearCrossFilter() }}
          role="img"
          aria-label="Agent throughput chart"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') clearCrossFilter() }}
        >
          <g transform={`translate(${CENTER},${CENTER})`}>
            {rings.map((ring) => (
              <path
                key={`bg-${ring.index}`}
                d={ring.bgPath}
                fill={ring.color}
                opacity={0.06}
              />
            ))}

            {rings.map((ring) => {
              const filterOpacity = getCrossFilterOpacity(
                crossFilter,
                { agent: ring.agent },
                'throughput'
              )

              return (
                <m.path
                  key={`fg-${ring.index}`}
                  d={ring.fgPath}
                  fill={ring.color}
                  initial={{ opacity: 0, pathLength: 0 }}
                  animate={{
                    opacity: filterOpacity * 0.85,
                    pathLength: 1,
                  }}
                  transition={{
                    opacity: { duration: 0.3 },
                    pathLength: {
                      duration: 0.8,
                      delay: ring.index * 0.08,
                      ease: 'easeOut',
                    },
                  }}
                  className="cursor-pointer"
                  style={{
                    filter: tooltip?.agent === ring.agent
                      ? `drop-shadow(0 0 6px ${ring.color})`
                      : 'none',
                    transition: 'filter 0.2s',
                  }}
                  onMouseEnter={(e) => handleRingHover(e, ring)}
                  onMouseLeave={handleRingLeave}
                  onClick={() => handleRingClick(ring)}
                />
              )
            })}

            <text
              x={0}
              y={-4}
              textAnchor="middle"
              dominantBaseline="central"
              style={{
                fontFamily: 'Inter',
                fontWeight: 700,
                fontSize: 22,
                fill: '#6366F1',
              }}
            >
              {formatNumber(totalTasks)}
            </text>
            <text
              x={0}
              y={16}
              textAnchor="middle"
              dominantBaseline="central"
              style={{
                fontFamily: '"JetBrains Mono"',
                fontSize: 8,
                fill: '#52525B',
                letterSpacing: '0.1em',
              }}
            >
              TASKS
            </text>
          </g>

          {rings.map((ring) => {
            const labelAngle = ring.endAngle - Math.PI / 2
            const labelR = ring.outerRadius + 10
            const lx = CENTER + Math.cos(labelAngle) * labelR
            const ly = CENTER + Math.sin(labelAngle) * labelR

            if (ring.endAngle < 0.3) return null

            return (
              <text
                key={`label-${ring.index}`}
                x={lx}
                y={ly}
                textAnchor="middle"
                dominantBaseline="central"
                style={{
                  fontFamily: '"JetBrains Mono"',
                  fontSize: 7,
                  fill: ring.color,
                  opacity: 0.7,
                }}
              >
                {ring.agent.slice(0, 3).toUpperCase()}
              </text>
            )
          })}
        </svg>
      </div>

      <div className="flex flex-wrap justify-center gap-3 mt-2">
        {rings.slice(0, 5).map((ring) => (
          <button
            key={`${ring.agent}-${ring.index}`}
            className="flex items-center gap-1.5 text-[10px] font-mono text-text-ghost hover:text-text-primary transition-colors"
            onClick={() => handleRingClick(ring)}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: ring.color }}
            />
            {ring.agent.replace(/_/g, ' ').slice(0, 12)}
          </button>
        ))}
        {rings.length > 5 && (
          <span className="text-[10px] font-mono text-text-ghost/50">+{rings.length - 5} more</span>
        )}
      </div>

      {tooltip && <ThroughputTooltip info={tooltip} x={tooltip.x} y={tooltip.y} />}
    </div>
  )
})
