import { m } from 'framer-motion'
import { X, Wrench, Users, ArrowUpRight } from 'lucide-react'
import { cn } from '../../utils/cn'
import GlassCard from '../shared/GlassCard'
import AgentAvatar from '../shared/AgentAvatar'
import TierBadge from '../shared/TierBadge'
import TraitBadge from '../shared/TraitBadge'
import StatusPill from '../shared/StatusPill'

// ── Tier label helpers ───────────────────────────────────────────────────────
const TIER_LABEL_MAP = {
  1: 'Supervisor',
  2: 'Lane Lead',
  3: 'Specialist',
  4: 'Foundation',
}

// ── Section heading ──────────────────────────────────────────────────────────
function SectionHeading({ children }) {
  return (
    <h4 className="text-xs font-mono text-text-ghost uppercase tracking-wider mb-2">
      {children}
    </h4>
  )
}

// ── Stat card ────────────────────────────────────────────────────────────────
function StatCard({ value, label }) {
  return (
    <div className="text-center p-3 rounded-lg bg-bg-subtle">
      <div className="text-lg font-display font-bold text-text-primary">{value}</div>
      <div className="text-xxs font-mono text-text-ghost uppercase">{label}</div>
    </div>
  )
}

// ── AgentDetailPanel ─────────────────────────────────────────────────────────
export default function AgentDetailPanel({ agent, onClose }) {
  if (!agent) return null

  const tierLabel = TIER_LABEL_MAP[agent.tier] || `Tier ${agent.tier}`
  const humanName = agent.human_name || agent.display_name || agent.name || 'Unknown'
  const role = agent.role || agent.display_name || ''
  const personality = agent.personality || agent.description || 'No personality description available.'
  const tasksToday = agent.tasks_today ?? 0
  const successRate = agent.success_rate ?? 0
  const avgMs = agent.avg_response_ms ?? 0
  const traits = agent.traits || []
  const tools = agent.tools || []
  const manages = agent.manages || []
  const reportsTo = agent.reports_to || null
  const expertise = agent.expertise || agent.capabilities || []

  return (
    <m.div
      key={agent.agent_key || agent.id}
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 16 }}
      transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
      className="h-full"
    >
      <GlassCard className="p-5 h-full overflow-y-auto relative" level="near">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-text-ghost hover:text-text-secondary hover:bg-bg-hover transition-colors"
          aria-label="Close panel"
        >
          <X className="w-4 h-4" />
        </button>

        {/* ── Agent Identity ─────────────────────────────────── */}
        <div className="flex items-center gap-4 mb-5 pr-8">
          <AgentAvatar
            name={humanName}
            tier={agent.tier}
            size="lg"
            status={agent.status}
          />
          <div className="min-w-0">
            <h2 className="text-lg font-display font-semibold text-text-primary truncate">
              {humanName}
            </h2>
            <p className="text-xs text-text-secondary truncate">{role}</p>
            <div className="flex items-center gap-2 mt-1">
              <TierBadge tier={agent.tier} label={tierLabel} />
              {agent.lane && (
                <span className="text-xxs font-mono text-text-ghost uppercase">
                  {agent.lane} lane
                </span>
              )}
            </div>
          </div>
        </div>

        {/* ── Personality ────────────────────────────────────── */}
        <div className="mb-5">
          <SectionHeading>Personality</SectionHeading>
          <p className="text-sm text-text-secondary leading-relaxed">{personality}</p>
        </div>

        {/* ── Stats Grid ─────────────────────────────────────── */}
        <div className="grid grid-cols-3 gap-3 mb-5">
          <StatCard value={tasksToday} label="Today" />
          <StatCard value={`${successRate}%`} label="Success" />
          <StatCard value={`${(avgMs / 1000).toFixed(1)}s`} label="Avg Time" />
        </div>

        {/* ── Traits ─────────────────────────────────────────── */}
        {traits.length > 0 && (
          <div className="mb-5">
            <SectionHeading>Traits</SectionHeading>
            <div className="flex flex-wrap gap-1.5">
              {traits.map((trait) => (
                <TraitBadge key={trait} trait={trait} />
              ))}
            </div>
          </div>
        )}

        {/* ── Tools ──────────────────────────────────────────── */}
        {tools.length > 0 && (
          <div className="mb-5">
            <SectionHeading>Tools</SectionHeading>
            <div className="space-y-1.5">
              {tools.map((tool) => (
                <div key={tool} className="flex items-center gap-2 text-xs text-text-secondary">
                  <Wrench className="w-3 h-3 text-text-ghost flex-shrink-0" />
                  <span className="font-mono">{tool}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Expertise / Capabilities ───────────────────────── */}
        {expertise.length > 0 && (
          <div className="mb-5">
            <SectionHeading>Expertise</SectionHeading>
            <div className="flex flex-wrap gap-1.5">
              {expertise.map((item) => (
                <span
                  key={item}
                  className={cn(
                    'inline-flex items-center rounded-full px-2 py-0.5',
                    'text-xxs font-medium',
                    'bg-teal-subtle text-teal border border-teal/10'
                  )}
                >
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ── Manages ────────────────────────────────────────── */}
        {manages.length > 0 && (
          <div className="mb-5">
            <SectionHeading>Manages</SectionHeading>
            <div className="space-y-1.5">
              {manages.map((agentKey) => (
                <div
                  key={agentKey}
                  className="flex items-center gap-2 text-xs text-text-secondary"
                >
                  <Users className="w-3 h-3 text-text-ghost flex-shrink-0" />
                  <span className="font-mono">
                    {agentKey.replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Reports To ─────────────────────────────────────── */}
        {reportsTo && (
          <div className="mb-5">
            <SectionHeading>Reports To</SectionHeading>
            <div className="flex items-center gap-2 text-xs text-text-secondary">
              <ArrowUpRight className="w-3 h-3 text-text-ghost flex-shrink-0" />
              <span className="font-mono">
                {reportsTo.replace(/_/g, ' ')}
              </span>
            </div>
          </div>
        )}

        {/* ── Status ─────────────────────────────────────────── */}
        <div>
          <SectionHeading>Status</SectionHeading>
          <StatusPill status={agent.status || 'idle'} />
        </div>
      </GlassCard>
    </m.div>
  )
}
