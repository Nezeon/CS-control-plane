import { useMemo, useRef, useEffect, useState, useCallback } from 'react'
import { m } from 'framer-motion'
import { cn } from '../../utils/cn'
import GlassCard from '../shared/GlassCard'
import AgentAvatar from '../shared/AgentAvatar'
import TierBadge from '../shared/TierBadge'

// ── Tier labels ─────────────────────────────────────────────────────────────
const TIER_LABELS = { 1: 'SUPERVISOR', 2: 'LANE LEADS', 3: 'SPECIALISTS', 4: 'FOUNDATION' }

// ── Lane display names (updated with function context) ──────────────────────
const LANE_LABELS = {
  support: 'Support (Troubleshooting)',
  value: 'Value (Adoption/QBR)',
  delivery: 'Delivery (Onboarding)',
}

// ── Lane hex colors for borders ─────────────────────────────────────────────
const LANE_HEX = { support: '#FFB547', value: '#00E5A0', delivery: '#3B9EFF' }

// ── Tier colors for SVG gradients & glows ───────────────────────────────────
const TIER_HEX = { 1: '#7C5CFC', 2: '#3B9EFF', 3: '#00E5C4', 4: '#5C5C72' }

// ── Tier border classes ─────────────────────────────────────────────────────
const TIER_BORDER = {
  1: 'border-tier-1',
  2: 'border-tier-2',
  3: 'border-tier-3',
  4: 'border-tier-4',
}

// ── Specialist short role labels ────────────────────────────────────────────
const SPECIALIST_SHORT_LABELS = {
  triage_agent: 'Ticket Triage',
  troubleshooter_agent: 'Troubleshooting',
  escalation_agent: 'Escalation Mgmt',
  health_monitor_agent: 'Health Analysis',
  fathom_agent: 'Fathom Agent',
  qbr_agent: 'QBR & Reviews',
  sow_agent: 'Scope & SOW',
  deployment_intel_agent: 'Deployment Intel',
}

// ── Tier section header with colored gradient lines ─────────────────────────
function TierHeader({ tier, label }) {
  const color = TIER_HEX[tier] || TIER_HEX[3]
  return (
    <div className="flex items-center gap-3 w-full max-w-xs">
      <div
        className="h-px flex-1"
        style={{ background: `linear-gradient(to right, transparent, ${color}40)` }}
      />
      <span
        className="font-mono text-[10px] font-semibold uppercase tracking-[0.15em]"
        style={{ color }}
      >
        {label}
      </span>
      <div
        className="h-px flex-1"
        style={{ background: `linear-gradient(to left, transparent, ${color}40)` }}
      />
    </div>
  )
}

// ── SVG animated connection line ────────────────────────────────────────────
function ConnectionLine({ x1, y1, x2, y2, fromTier, toTier, isActive }) {
  const gradientId = `grad-${x1}-${y1}-${x2}-${y2}`.replace(/[^a-zA-Z0-9-]/g, '')
  const fromColor = TIER_HEX[fromTier] || TIER_HEX[3]
  const toColor = TIER_HEX[toTier] || TIER_HEX[3]

  const isStraight = Math.abs(x1 - x2) < 2
  const midY = (y1 + y2) / 2

  const pathD = isStraight
    ? `M ${x1} ${y1} L ${x2} ${y2}`
    : `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`

  return (
    <g>
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={fromColor} stopOpacity={isActive ? 0.9 : 0.3} />
          <stop offset="100%" stopColor={toColor} stopOpacity={isActive ? 0.9 : 0.3} />
        </linearGradient>
      </defs>

      {/* Glow layer */}
      {isActive && (
        <path
          d={pathD}
          fill="none"
          stroke={fromColor}
          strokeWidth={5}
          opacity={0.12}
          className="animate-connection-glow"
        />
      )}

      {/* Main line */}
      <path
        d={pathD}
        fill="none"
        stroke={`url(#${gradientId})`}
        strokeWidth={isActive ? 2 : 1.5}
        strokeLinecap="round"
      />

      {/* Animated dash overlay for active connections */}
      {isActive && (
        <path
          d={pathD}
          fill="none"
          stroke={toColor}
          strokeWidth={2}
          strokeLinecap="round"
          strokeDasharray="4 8"
          opacity={0.7}
          className="animate-connection-flow"
        />
      )}
    </g>
  )
}

// ── Agent node ──────────────────────────────────────────────────────────────
function AgentNode({ agent, compact = false, selected, onClick, nodeRef }) {
  const isActive = agent.status === 'active' || agent.status === 'processing'
  const tierColor = TIER_HEX[agent.tier] || TIER_HEX[3]
  const tierBorder = TIER_BORDER[agent.tier] || TIER_BORDER[3]

  return (
    <m.button
      ref={nodeRef}
      onClick={() => onClick(agent.agent_key || agent.name || agent.id)}
      whileHover={{ scale: 1.05, y: -2 }}
      whileTap={{ scale: 0.97 }}
      transition={{ type: 'spring', stiffness: 400, damping: 20 }}
      className={cn(
        'relative flex flex-col items-center gap-1.5 rounded-xl border transition-all cursor-pointer',
        'border-t-2',
        tierBorder,
        compact ? 'p-3 px-4' : 'p-4 px-5',
        selected
          ? 'border-accent bg-accent-subtle border-t-accent'
          : 'border-border-subtle hover:border-border bg-bg-card/50 hover:bg-bg-hover',
      )}
      style={isActive ? {
        boxShadow: `0 0 16px ${tierColor}25`,
        borderColor: undefined,
      } : undefined}
      data-agent-key={agent.agent_key || agent.name || agent.id}
      data-tier={agent.tier}
    >
      {/* Active pulse ring */}
      {isActive && (
        <span
          className="absolute -inset-px rounded-xl animate-pulse-ring"
          style={{
            boxShadow: `0 0 12px ${tierColor}40`,
          }}
        />
      )}

      <AgentAvatar
        name={agent.human_name || agent.display_name || agent.name}
        tier={agent.tier}
        size={compact ? 'md' : 'lg'}
        status={agent.status}
      />
      <span
        className={cn(
          'font-medium text-text-primary leading-tight text-center',
          compact ? 'text-xs' : 'text-sm'
        )}
      >
        {(agent.human_name || agent.display_name || '').split(' ')[0]}
      </span>
      {!compact && (
        <>
          {agent.role && (
            <span className="text-xxs text-text-muted text-center leading-snug max-w-[120px] truncate">
              {agent.role}
            </span>
          )}
          <TierBadge tier={agent.tier} />
          <span className="text-xxs text-text-ghost font-mono tabular-nums">
            {agent.tasks_today ?? 0} tasks
          </span>
        </>
      )}
    </m.button>
  )
}

// ── Lane column: a T2 lead + their T3 specialists ───────────────────────────
function LaneColumn({ lead, specialists, laneName, selectedAgent, onAgentClick, leadRef, specRefs }) {
  const laneColor = LANE_HEX[laneName] || '#5C5C72'

  return (
    <div
      className="glass-far flex flex-col items-center gap-4 px-5 py-5 rounded-2xl"
      style={{ borderTop: `2px solid ${laneColor}` }}
    >
      {/* Lane label */}
      <span
        className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-center"
        style={{ color: laneColor }}
      >
        {LANE_LABELS[laneName] || laneName}
      </span>

      {/* Lane lead node */}
      <AgentNode
        agent={lead}
        selected={selectedAgent === (lead.agent_key || lead.name)}
        onClick={onAgentClick}
        nodeRef={leadRef}
      />

      {/* Specialist nodes with role labels */}
      {specialists.length > 0 && (
        <div className="flex gap-4 flex-wrap justify-center">
          {specialists.map((spec) => {
            const specKey = spec.agent_key || spec.name || spec.id
            const roleLabel = SPECIALIST_SHORT_LABELS[spec.agent_key] || ''
            return (
              <div key={spec.id || spec.agent_key} className="flex flex-col items-center gap-1.5">
                {roleLabel && (
                  <span className="text-[9px] font-mono text-text-ghost uppercase tracking-wider text-center leading-tight">
                    {roleLabel}
                  </span>
                )}
                <AgentNode
                  agent={spec}
                  compact
                  selected={selectedAgent === specKey}
                  onClick={onAgentClick}
                  nodeRef={(el) => {
                    if (specRefs) specRefs.current[specKey] = el
                  }}
                />
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ── HierarchyTree — the full 4-tier org chart with animated SVG connections ─
export default function HierarchyTree({ agents = [], selectedAgent, onAgentClick }) {
  const containerRef = useRef(null)
  const supervisorRef = useRef(null)
  const leadRefs = useRef({})
  const specRefs = useRef({})
  const foundationRefs = useRef({})
  const [connections, setConnections] = useState([])
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 })

  // Group agents by tier and lane
  const { supervisor, lanes, foundation } = useMemo(() => {
    const tier1 = agents.filter((a) => a.tier === 1)
    const tier2 = agents.filter((a) => a.tier === 2)
    const tier3 = agents.filter((a) => a.tier === 3)
    const tier4 = agents.filter((a) => a.tier === 4)

    const laneMap = {}
    for (const lead of tier2) {
      const lane = lead.lane || 'unknown'
      const managedKeys = lead.manages || []
      const specs = tier3.filter(
        (s) =>
          s.reports_to === (lead.agent_key || lead.name) ||
          managedKeys.includes(s.agent_key || s.name) ||
          s.lane === lane
      )
      const seenKeys = new Set()
      const uniqueSpecs = specs.filter((s) => {
        const key = s.agent_key || s.name || s.id
        if (seenKeys.has(key)) return false
        seenKeys.add(key)
        return true
      })
      laneMap[lane] = { lead, specialists: uniqueSpecs }
    }

    const laneOrder = ['support', 'value', 'delivery']
    const orderedLanes = laneOrder
      .filter((l) => laneMap[l])
      .map((l) => ({ name: l, ...laneMap[l] }))

    for (const [laneKey, laneData] of Object.entries(laneMap)) {
      if (!laneOrder.includes(laneKey)) {
        orderedLanes.push({ name: laneKey, ...laneData })
      }
    }

    return {
      supervisor: tier1[0] || null,
      lanes: orderedLanes,
      foundation: tier4,
    }
  }, [agents])

  // Calculate SVG connection paths after DOM layout
  const calculateConnections = useCallback(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    const containerRect = container.getBoundingClientRect()
    const conns = []

    const getBottom = (el) => {
      if (!el) return null
      const rect = el.getBoundingClientRect()
      return {
        x: rect.left + rect.width / 2 - containerRect.left,
        y: rect.bottom - containerRect.top,
      }
    }

    const getTop = (el) => {
      if (!el) return null
      const rect = el.getBoundingClientRect()
      return {
        x: rect.left + rect.width / 2 - containerRect.left,
        y: rect.top - containerRect.top,
      }
    }

    // T1 → T2 connections
    if (supervisorRef.current) {
      const supBottom = getBottom(supervisorRef.current)
      if (supBottom) {
        for (const lane of lanes) {
          const leadKey = lane.lead.agent_key || lane.lead.name
          const leadEl = leadRefs.current[leadKey]
          if (leadEl) {
            const leadTop = getTop(leadEl)
            if (leadTop) {
              const isActive =
                supervisor?.status === 'active' || lane.lead.status === 'active'
              conns.push({
                x1: supBottom.x,
                y1: supBottom.y + 4,
                x2: leadTop.x,
                y2: leadTop.y - 4,
                fromTier: 1,
                toTier: 2,
                isActive,
                key: `t1-${leadKey}`,
              })
            }
          }

          // T2 → T3 connections
          for (const spec of lane.specialists) {
            const specKey = spec.agent_key || spec.name || spec.id
            const specEl = specRefs.current[specKey]
            const leadEl2 = leadRefs.current[leadKey]
            if (leadEl2 && specEl) {
              const leadBottom2 = getBottom(leadEl2)
              const specTop = getTop(specEl)
              if (leadBottom2 && specTop) {
                const isActive =
                  lane.lead.status === 'active' || spec.status === 'active'
                conns.push({
                  x1: leadBottom2.x,
                  y1: leadBottom2.y + 4,
                  x2: specTop.x,
                  y2: specTop.y - 4,
                  fromTier: 2,
                  toTier: 3,
                  isActive,
                  key: `t2-${leadKey}-${specKey}`,
                })
              }
            }
          }
        }
      }
    }

    // T3/T2 → T4 connections
    if (supervisorRef.current && foundation.length > 0) {
      for (const f of foundation) {
        const fKey = f.agent_key || f.name || f.id
        const fEl = foundationRefs.current[fKey]
        if (fEl) {
          const fTop = getTop(fEl)
          if (fTop) {
            const centerX = containerRect.width / 2
            conns.push({
              x1: centerX,
              y1: fTop.y - 20,
              x2: fTop.x,
              y2: fTop.y - 4,
              fromTier: 3,
              toTier: 4,
              isActive: false,
              key: `t4-${fKey}`,
            })
          }
        }
      }
    }

    setConnections(conns)
    setContainerSize({ width: containerRect.width, height: containerRect.height })
  }, [supervisor, lanes, foundation])

  // Recalculate on mount, resize, and agent changes
  useEffect(() => {
    const timer = setTimeout(calculateConnections, 100)
    const resizeObserver = new ResizeObserver(() => {
      requestAnimationFrame(calculateConnections)
    })
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current)
    }
    return () => {
      clearTimeout(timer)
      resizeObserver.disconnect()
    }
  }, [calculateConnections, agents])

  if (agents.length === 0) {
    return (
      <GlassCard className="p-6 h-full flex items-center justify-center">
        <p className="text-sm text-text-ghost font-mono">No agents available</p>
      </GlassCard>
    )
  }

  return (
    <GlassCard className="p-8 h-full overflow-auto">
      <h3 className="text-base font-display font-semibold text-text-primary mb-8 text-center">
        Organization Hierarchy
      </h3>

      <div ref={containerRef} className="relative flex flex-col items-center gap-8">
        {/* ── SVG connection layer ─────────────────────────────── */}
        {containerSize.width > 0 && (
          <svg
            className="absolute inset-0 pointer-events-none z-0"
            width={containerSize.width}
            height={containerSize.height}
            style={{ overflow: 'visible' }}
          >
            {connections.map(({ key, ...rest }) => (
              <ConnectionLine key={key} {...rest} />
            ))}
          </svg>
        )}

        {/* ── Tier 1: Supervisor ──────────────────────────────── */}
        {supervisor && (
          <m.div
            className="relative z-10 flex flex-col items-center gap-3"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <TierHeader tier={1} label={TIER_LABELS[1]} />
            <AgentNode
              agent={supervisor}
              selected={selectedAgent === (supervisor.agent_key || supervisor.name)}
              onClick={onAgentClick}
              nodeRef={supervisorRef}
            />
          </m.div>
        )}

        {/* ── Tier 2 + Tier 3: Lane columns ──────────────────── */}
        {lanes.length > 0 && (
          <m.div
            className="relative z-10 flex flex-col items-center gap-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.15 }}
          >
            <TierHeader tier={2} label={TIER_LABELS[2]} />
            <div className="flex items-start gap-5 sm:gap-6 lg:gap-8">
              {lanes.map((lane) => {
                const leadKey = lane.lead.agent_key || lane.lead.name
                return (
                  <LaneColumn
                    key={lane.name}
                    lead={lane.lead}
                    specialists={lane.specialists}
                    laneName={lane.name}
                    selectedAgent={selectedAgent}
                    onAgentClick={onAgentClick}
                    leadRef={(el) => {
                      leadRefs.current[leadKey] = el
                    }}
                    specRefs={specRefs}
                  />
                )
              })}
            </div>
          </m.div>
        )}

        {/* ── Tier 4: Foundation ──────────────────────────────── */}
        {foundation.length > 0 && (
          <m.div
            className="relative z-10 flex flex-col items-center gap-3 mt-2"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <TierHeader tier={4} label={TIER_LABELS[4]} />
            <div className="flex gap-3">
              {foundation.map((agent) => {
                const fKey = agent.agent_key || agent.name || agent.id
                return (
                  <AgentNode
                    key={agent.id || agent.agent_key}
                    agent={agent}
                    selected={selectedAgent === fKey}
                    onClick={onAgentClick}
                    nodeRef={(el) => {
                      foundationRefs.current[fKey] = el
                    }}
                  />
                )
              })}
            </div>
          </m.div>
        )}
      </div>
    </GlassCard>
  )
}
