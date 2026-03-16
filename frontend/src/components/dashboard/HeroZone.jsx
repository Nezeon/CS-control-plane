import { lazy, Suspense, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { m } from 'framer-motion'
import useDashboardStore from '../../stores/dashboardStore'
import useSettingsStore from '../../stores/settingsStore'
import AnimatedCounter from '../shared/AnimatedCounter'
import HealthRing from '../shared/HealthRing'
import AgentAvatar from '../shared/AgentAvatar'
import { Users, AlertTriangle, Ticket, Activity } from 'lucide-react'

const NeuralSphere = lazy(() => import('../../three/NeuralSphere'))

const TIER_DOT_COLORS = {
  1: '#7C5CFC',
  2: '#3B9EFF',
  3: '#00E5C4',
  4: '#5C5C72',
}

function KpiOrb({ value, label, icon: Icon, color, className, children }) {
  return (
    <m.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className={`absolute z-20 w-fit ${className}`}
    >
      <div
        className="w-[104px] h-[104px] rounded-full flex flex-col items-center justify-center backdrop-blur-xl border border-white/[0.08]"
        style={{
          background: `radial-gradient(circle at 30% 30%, ${color}18, rgba(5,5,7,0.88))`,
          boxShadow: `0 0 30px ${color}25, 0 0 60px ${color}10, inset 0 0 24px ${color}0a`,
        }}
      >
        {children || (
          <>
            <Icon size={16} style={{ color }} className="mb-1 opacity-80" />
            <AnimatedCounter
              value={value}
              className="font-display text-2xl font-bold text-text-primary"
            />
          </>
        )}
      </div>
      <p className="text-center text-xxs text-text-ghost font-mono mt-2 tracking-wider">
        {label}
      </p>
    </m.div>
  )
}

function Agent2DFallback({ agents, navigate }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center p-8">
      <div className="grid grid-cols-5 gap-3 max-w-[600px]">
        {agents.map((agent) => (
          <button
            key={agent.id || agent.name}
            onClick={() => navigate('/agents')}
            className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-bg-active/30 border border-border-subtle hover:border-accent/20 transition-all"
          >
            <AgentAvatar
              name={agent.human_name || agent.display_name || agent.name}
              tier={agent.tier || 3}
              size="sm"
              status={agent.status}
            />
            <span className="text-xxs text-text-ghost truncate max-w-full">
              {(agent.human_name || agent.display_name || agent.name || '').replace('CS ', '').replace(' Agent', '')}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

function AgentStatusStrip({ agents, navigate }) {
  return (
    <div className="absolute bottom-0 left-0 right-0 z-20">
      <div className="flex items-center justify-center gap-1 px-4 py-2.5 bg-gradient-to-t from-[rgba(5,5,7,0.9)] to-transparent">
        <button
          onClick={() => navigate('/agents')}
          className="flex items-center gap-1.5 group"
        >
          {agents.map((agent) => {
            const tier = agent.tier || 3
            const color = TIER_DOT_COLORS[tier] || TIER_DOT_COLORS[3]
            const isActive = agent.status === 'active' || agent.status === 'processing'
            const size = tier === 1 ? 10 : tier === 2 ? 8 : 6

            return (
              <span
                key={agent.id || agent.name}
                title={`${agent.human_name || agent.name} — ${agent.status}`}
                className="relative inline-block transition-transform group-hover:scale-110"
                style={{ width: size, height: size }}
              >
                <span
                  className="absolute inset-0 rounded-full"
                  style={{
                    background: color,
                    opacity: isActive ? 1 : 0.3,
                    boxShadow: isActive ? `0 0 6px ${color}80` : 'none',
                  }}
                />
                {isActive && (
                  <span
                    className="absolute inset-0 rounded-full animate-pulse-ring"
                    style={{ border: `1px solid ${color}`, opacity: 0.4 }}
                  />
                )}
              </span>
            )
          })}
        </button>
        <span className="text-xxs text-text-ghost font-mono ml-3">
          {agents.filter((a) => a.status === 'active' || a.status === 'processing').length}/{agents.length} active
        </span>
      </div>
    </div>
  )
}

export default function HeroZone() {
  const stats = useDashboardStore((s) => s.stats)
  const agents = useDashboardStore((s) => s.agents)
  const navigate = useNavigate()
  const reducedMotion = useSettingsStore?.((s) => s.reducedMotion) ?? false

  const avgHealth = useMemo(() => {
    const v = stats?.avg_health_score ?? stats?.avg_health
    return v != null ? Math.round(v) : 0
  }, [stats])

  const atRisk = stats?.at_risk_count ?? stats?.high_risk ?? 0
  const totalCustomers = stats?.total_customers ?? 0
  const openTickets = stats?.open_tickets ?? stats?.total_tickets_open ?? 0

  return (
    <div className="relative rounded-2xl overflow-hidden gradient-border" style={{ height: 420 }}>
      {/* Atmospheric inner glow */}
      <div
        className="absolute inset-0 pointer-events-none z-0"
        style={{
          background: `
            radial-gradient(ellipse 50% 50% at 50% 50%, rgba(124,92,252,0.06) 0%, transparent 70%),
            radial-gradient(ellipse 40% 60% at 80% 30%, rgba(0,229,196,0.04) 0%, transparent 60%),
            rgba(5,5,7,1)
          `,
        }}
      />

      {/* 3D Scene / 2D Fallback */}
      <div className="absolute inset-0 z-10">
        {reducedMotion ? (
          <Agent2DFallback agents={agents || []} navigate={navigate} />
        ) : (
          <Suspense fallback={<Agent2DFallback agents={agents || []} navigate={navigate} />}>
            {agents?.length > 0 && (
              <NeuralSphere agents={agents} onAgentClick={() => navigate('/agents')} />
            )}
          </Suspense>
        )}
      </div>

      {/* Floating KPI Orbs */}
      <KpiOrb
        value={totalCustomers}
        label="CUSTOMERS"
        icon={Users}
        color="#7C5CFC"
        className="top-4 left-4"
      />

      <KpiOrb
        label="AVG HEALTH"
        icon={Activity}
        color="#00E5C4"
        className="top-4 right-4"
      >
        <HealthRing score={avgHealth} size={58} strokeWidth={3} />
      </KpiOrb>

      <KpiOrb
        value={atRisk}
        label="AT RISK"
        icon={AlertTriangle}
        color="#FF5C5C"
        className="bottom-14 left-4"
      />

      <KpiOrb
        value={openTickets}
        label="TICKETS"
        icon={Ticket}
        color="#3B9EFF"
        className="bottom-14 right-4"
      />

      {/* Agent Status Strip */}
      {agents?.length > 0 && (
        <AgentStatusStrip agents={agents} navigate={navigate} />
      )}

      {/* Top edge glow */}
      <div className="absolute top-0 left-1/4 right-1/4 h-px bg-gradient-to-r from-transparent via-accent/30 to-transparent z-30 pointer-events-none" />
    </div>
  )
}
