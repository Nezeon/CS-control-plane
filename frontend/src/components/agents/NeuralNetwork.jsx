import { useState, useMemo, useCallback } from 'react'
import { m } from 'framer-motion'
import { getLaneColor, getStatusHex, getInitials } from '../../utils/formatters'

const EMPTY_ARRAY = []

/* ─── Agent layout positions by lane cluster ─── */
const LAYOUT = {
  orchestrator:     { x: 500, y: 340, r: 44 },
  memory_agent:     { x: 500, y: 140, r: 28, lane: 'control' },
  health_monitor:   { x: 340, y: 180, r: 28, lane: 'control' },
  escalation_agent: { x: 660, y: 180, r: 28, lane: 'control' },
  fathom:           { x: 780, y: 320, r: 26, lane: 'value' },
  qbr_generator:    { x: 760, y: 480, r: 26, lane: 'value' },
  ticket_triage:    { x: 180, y: 300, r: 26, lane: 'support' },
  troubleshooter:   { x: 200, y: 460, r: 26, lane: 'support' },
  sow_analyzer:     { x: 400, y: 540, r: 24, lane: 'delivery' },
  deployment_intel:  { x: 600, y: 540, r: 24, lane: 'delivery' },
}

function getNodeLayout(agentName) {
  const key = agentName?.toLowerCase().replace(/\s+/g, '_')
  return LAYOUT[key] || null
}

/* ─── Bezier path from orchestrator to node ─── */
function connectionPath(ox, oy, nx, ny) {
  const mx = (ox + nx) / 2
  const my = (oy + ny) / 2
  const cpx = mx + (ny - oy) * 0.15
  const cpy = my - (nx - ox) * 0.15
  return `M ${ox} ${oy} Q ${cpx} ${cpy} ${nx} ${ny}`
}

/* ─── Animated dashed connection line ─── */
function ConnectionLine({ ox, oy, nx, ny, color, active }) {
  const d = connectionPath(ox, oy, nx, ny)
  return (
    <g>
      <path
        d={d}
        fill="none"
        stroke={`${color}20`}
        strokeWidth={1.5}
      />
      <path
        d={d}
        fill="none"
        stroke={active ? color : `${color}40`}
        strokeWidth={active ? 1.8 : 1}
        strokeDasharray={active ? '6 4' : '4 8'}
        style={active ? {
          animation: 'dashFlow 1.5s linear infinite',
        } : undefined}
      />
    </g>
  )
}

/* ─── Agent node circle ─── */
function AgentNode({ agent, layout, isSelected, isAnySelected, onHover, onLeave, onClick }) {
  const { x, y, r, lane } = layout
  const laneColor = lane ? getLaneColor(lane) : '#7C5CFC'
  const statusColor = getStatusHex(agent.status)
  const isActive = agent.status === 'active' || agent.status === 'processing'
  const initials = getInitials(agent.display_name || agent.name)
  const dimmed = isAnySelected && !isSelected

  return (
    <m.g
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{
        opacity: dimmed ? 0.3 : 1,
        scale: 1,
      }}
      transition={{ type: 'spring', stiffness: 260, damping: 20, delay: Math.random() * 0.3 }}
      style={{ cursor: 'pointer' }}
      onMouseEnter={() => onHover(agent)}
      onMouseLeave={onLeave}
      onClick={() => onClick(agent)}
    >
      {/* Pulse ring for active agents */}
      {isActive && (
        <circle
          cx={x} cy={y} r={r + 6}
          fill="none"
          stroke={statusColor}
          strokeWidth={2}
          opacity={0.3}
          style={{ animation: 'pulseGlow 2s ease-in-out infinite' }}
        />
      )}

      {/* Selection highlight */}
      {isSelected && (
        <circle
          cx={x} cy={y} r={r + 10}
          fill="none"
          stroke={laneColor}
          strokeWidth={2}
          strokeDasharray="4 3"
          opacity={0.6}
        />
      )}

      {/* Main circle */}
      <circle
        cx={x} cy={y} r={r}
        fill="#09090B"
        stroke={laneColor}
        strokeWidth={isSelected ? 2.5 : 1.5}
        style={{ transition: 'stroke 0.3s ease, stroke-width 0.3s ease' }}
      />

      {/* Status dot (top-right) */}
      <circle
        cx={x + r * 0.65} cy={y - r * 0.65} r={4}
        fill={statusColor}
      />

      {/* Initials */}
      <text
        x={x} y={y + 1}
        textAnchor="middle"
        dominantBaseline="central"
        className="font-semibold select-none pointer-events-none"
        style={{
          fill: laneColor,
          fontSize: r * 0.55,
          fontFamily: 'Inter',
          letterSpacing: '0.05em',
        }}
      >
        {initials}
      </text>

      {/* Name label below */}
      <text
        x={x} y={y + r + 14}
        textAnchor="middle"
        className="select-none pointer-events-none"
        style={{
          fill: '#5C5C72',
          fontSize: 10,
          fontFamily: '"JetBrains Mono"',
          letterSpacing: '0.03em',
        }}
      >
        {(agent.display_name || agent.name || '').replace(/_/g, ' ')}
      </text>

      {/* Tasks count badge */}
      {agent.tasks_today > 0 && (
        <g>
          <rect
            x={x - 12} y={y + r + 20}
            width={24} height={14}
            rx={7}
            fill={`${laneColor}20`}
            stroke={`${laneColor}40`}
            strokeWidth={0.5}
          />
          <text
            x={x} y={y + r + 28}
            textAnchor="middle"
            dominantBaseline="central"
            className="select-none pointer-events-none"
            style={{ fill: laneColor, fontSize: 9, fontFamily: '"JetBrains Mono"' }}
          >
            {agent.tasks_today}
          </text>
        </g>
      )}
    </m.g>
  )
}

/* ─── Tooltip overlay ─── */
function Tooltip({ agent, layout }) {
  if (!agent || !layout) return null
  const { x, y, r } = layout
  const tx = x + r + 20
  const ty = Math.max(60, y - 40)

  return (
    <m.foreignObject
      x={tx} y={ty}
      width={200} height={120}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.15 }}
      style={{ pointerEvents: 'none' }}
    >
      <div className="bg-bg-elevated rounded-lg p-3 border border-border text-xs">
        <div className="text-sm text-text-primary font-semibold mb-1">
          {(agent.display_name || agent.name || '').replace(/_/g, ' ')}
        </div>
        <div className="text-text-ghost font-mono space-y-0.5">
          <div>Status: <span style={{ color: getStatusHex(agent.status) }}>{agent.status}</span></div>
          {agent.lane && <div>Lane: {agent.lane}</div>}
          {agent.tasks_today != null && <div>Tasks today: {agent.tasks_today}</div>}
          {agent.avg_response_ms != null && <div>Avg: {(agent.avg_response_ms / 1000).toFixed(1)}s</div>}
          {agent.success_rate != null && <div>Success: {agent.success_rate}%</div>}
        </div>
      </div>
    </m.foreignObject>
  )
}

/* ─── Main SVG Component ─── */
export default function NeuralNetwork({ agents = EMPTY_ARRAY, selectedAgent, onAgentClick }) {
  const [hoveredAgent, setHoveredAgent] = useState(null)

  const orchLayout = LAYOUT.orchestrator

  const agentNodes = useMemo(() => {
    return agents.map((agent) => {
      const layout = getNodeLayout(agent.name)
      return layout ? { agent, layout } : null
    }).filter(Boolean)
  }, [agents])

  const handleClick = useCallback((agent) => {
    onAgentClick?.(agent.name)
  }, [onAgentClick])

  const handleHover = useCallback((agent) => setHoveredAgent(agent), [])
  const handleLeave = useCallback(() => setHoveredAgent(null), [])

  const hoveredLayout = hoveredAgent ? getNodeLayout(hoveredAgent.name) : null

  return (
    <div data-testid="neural-network" className="relative w-full h-full">
      <style>{`
        @keyframes dashFlow {
          to { stroke-dashoffset: -20; }
        }
        @keyframes pulseGlow {
          0%, 100% { opacity: 0.2; }
          50% { opacity: 0.5; }
        }
      `}</style>

      <svg
        viewBox="0 0 1000 680"
        className="w-full h-full"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(63,63,70,0.15)" strokeWidth="0.5" />
          </pattern>
          <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#7C5CFC" stopOpacity="0.06" />
            <stop offset="100%" stopColor="#7C5CFC" stopOpacity="0" />
          </radialGradient>
        </defs>

        <rect width="1000" height="680" fill="url(#grid)" />
        <circle cx="500" cy="340" r="250" fill="url(#centerGlow)" />

        {agentNodes.map(({ agent, layout }) => {
          const isActive = agent.status === 'active' || agent.status === 'processing'
          const laneColor = layout.lane ? getLaneColor(layout.lane) : '#7C5CFC'
          return (
            <ConnectionLine
              key={`conn-${agent.name}`}
              ox={orchLayout.x}
              oy={orchLayout.y}
              nx={layout.x}
              ny={layout.y}
              color={laneColor}
              active={isActive}
            />
          )
        })}

        <text x="500" y="80" textAnchor="middle" style={{ fontFamily: '"JetBrains Mono"', fill: '#7C5CFC20', fontSize: 11, letterSpacing: '0.2em' }}>CONTROL</text>
        <text x="860" y="400" textAnchor="middle" style={{ fontFamily: '"JetBrains Mono"', fill: '#00E5A020', fontSize: 11, letterSpacing: '0.2em' }}>VALUE</text>
        <text x="120" y="380" textAnchor="middle" style={{ fontFamily: '"JetBrains Mono"', fill: '#FFB54720', fontSize: 11, letterSpacing: '0.2em' }}>SUPPORT</text>
        <text x="500" y="630" textAnchor="middle" style={{ fontFamily: '"JetBrains Mono"', fill: '#3B9EFF20', fontSize: 11, letterSpacing: '0.2em' }}>DELIVERY</text>

        {agentNodes.map(({ agent, layout }) => (
          <AgentNode
            key={agent.name}
            agent={agent}
            layout={layout}
            isSelected={selectedAgent === agent.name}
            isAnySelected={!!selectedAgent}
            onHover={handleHover}
            onLeave={handleLeave}
            onClick={handleClick}
          />
        ))}

        <m.g
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.1 }}
        >
          <circle
            cx={orchLayout.x} cy={orchLayout.y} r={orchLayout.r + 8}
            fill="none"
            stroke="#7C5CFC"
            strokeWidth={1}
            opacity={0.15}
            style={{ animation: 'pulseGlow 3s ease-in-out infinite' }}
          />
          <circle
            cx={orchLayout.x} cy={orchLayout.y} r={orchLayout.r}
            fill="rgba(124,92,252,0.08)"
            stroke="#7C5CFC"
            strokeWidth={2}
          />
          <text
            x={orchLayout.x} y={orchLayout.y - 6}
            textAnchor="middle"
            dominantBaseline="central"
            className="font-bold select-none pointer-events-none"
            style={{ fill: '#7C5CFC', fontSize: 14, fontFamily: 'Inter' }}
          >
            ORCH
          </text>
          <text
            x={orchLayout.x} y={orchLayout.y + 10}
            textAnchor="middle"
            dominantBaseline="central"
            className="select-none pointer-events-none"
            style={{ fill: 'rgba(124,92,252,0.5)', fontSize: 9, fontFamily: '"JetBrains Mono"' }}
          >
            ORCHESTRATOR
          </text>
        </m.g>

        {hoveredAgent && hoveredLayout && (
          <Tooltip agent={hoveredAgent} layout={hoveredLayout} />
        )}
      </svg>
    </div>
  )
}
