import { useState } from 'react'
import { m } from 'framer-motion'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Zap,
  Timer,
  CheckCircle2,
  Activity,
} from 'lucide-react'
import { cn } from '../utils/cn'
import GlassCard from '../components/shared/GlassCard'
import AgentAvatar from '../components/shared/AgentAvatar'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

// ── Seed data ───────────────────────────────────────────────────────────────

const healthTrend = [
  { day: 'Mon', avg: 68 },
  { day: 'Tue', avg: 71 },
  { day: 'Wed', avg: 65 },
  { day: 'Thu', avg: 69 },
  { day: 'Fri', avg: 72 },
  { day: 'Sat', avg: 73 },
  { day: 'Sun', avg: 70 },
]

const ticketVolume = [
  { day: 'Mon', P1: 2, P2: 5, P3: 8, P4: 3 },
  { day: 'Tue', P1: 1, P2: 3, P3: 6, P4: 4 },
  { day: 'Wed', P1: 3, P2: 6, P3: 9, P4: 2 },
  { day: 'Thu', P1: 1, P2: 4, P3: 7, P4: 5 },
  { day: 'Fri', P1: 2, P2: 3, P3: 5, P4: 3 },
  { day: 'Sat', P1: 0, P2: 1, P3: 2, P4: 1 },
  { day: 'Sun', P1: 1, P2: 2, P3: 3, P4: 2 },
]

const agentPerformance = [
  { name: 'Naveen Kapoor', role: 'Supervisor', tasks: 56, avgTime: '0.8m', accuracy: 99, tier: 1 },
  { name: 'Atlas', role: 'Memory', tasks: 156, avgTime: '0.3m', accuracy: 99, tier: 4 },
  { name: 'Dr. Aisha Okafor', role: 'Health Monitor', tasks: 87, avgTime: '1.2m', accuracy: 98, tier: 3 },
  { name: 'Kai Nakamura', role: 'Triage', tasks: 42, avgTime: '2.3m', accuracy: 94, tier: 3 },
  { name: 'Rachel Torres', role: 'Support Lead', tasks: 34, avgTime: '1.8m', accuracy: 95, tier: 2 },
  { name: 'Damon Reeves', role: 'Value Lead', tasks: 29, avgTime: '2.1m', accuracy: 96, tier: 2 },
  { name: 'Leo Petrov', role: 'Troubleshooter', tasks: 28, avgTime: '8.1m', accuracy: 91, tier: 3 },
  { name: 'Jordan Ellis', role: 'Fathom', tasks: 23, avgTime: '5.7m', accuracy: 93, tier: 3 },
  { name: 'Priya Mehta', role: 'Delivery Lead', tasks: 22, avgTime: '2.4m', accuracy: 94, tier: 2 },
  { name: 'Zara Kim', role: 'Deployment', tasks: 18, avgTime: '4.2m', accuracy: 97, tier: 3 },
  { name: 'Maya Santiago', role: 'Escalation', tasks: 15, avgTime: '4.5m', accuracy: 96, tier: 3 },
  { name: 'Ethan Brooks', role: 'SOW', tasks: 12, avgTime: '6.8m', accuracy: 92, tier: 3 },
  { name: 'Sofia Marquez', role: 'QBR', tasks: 8, avgTime: '12.4m', accuracy: 94, tier: 3 },
]

const pipelineStats = [
  { label: 'Total Pipelines', value: '584', change: '+12%', positive: true, Icon: Activity },
  { label: 'Avg Duration', value: '4.2m', change: '-8%', positive: true, Icon: Timer },
  { label: 'Success Rate', value: '94.6%', change: '+1.2%', positive: true, Icon: CheckCircle2 },
  { label: 'Tokens Used', value: '1.2M', change: '+15%', positive: false, Icon: Zap },
]

const sentimentDist = [
  { name: 'Very Positive', value: 12, color: '#00E5A0' },
  { name: 'Positive', value: 28, color: '#4DD5B8' },
  { name: 'Mixed', value: 18, color: '#FFB547' },
  { name: 'Negative', value: 8, color: '#FF8C5C' },
  { name: 'Very Negative', value: 4, color: '#FF5C5C' },
]

const totalCalls = sentimentDist.reduce((s, d) => s + d.value, 0)

// ── Custom tooltip ──────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg px-3 py-2 text-xs border bg-[#0A1628] border-white/10 shadow-xl">
      <p className="text-text-muted font-mono mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} className="text-text-primary">
          <span style={{ color: p.color }}>{p.dataKey}:</span> {p.value}
        </p>
      ))}
    </div>
  )
}

// ── Accuracy color ──────────────────────────────────────────────────────────

function accuracyColor(acc) {
  if (acc >= 97) return 'text-status-success'
  if (acc >= 93) return 'text-teal'
  if (acc >= 90) return 'text-status-warning'
  return 'text-status-danger'
}

// ── Axis config ─────────────────────────────────────────────────────────────

const axisStyle = {
  fontSize: 11,
  fontFamily: "'JetBrains Mono', monospace",
  fill: 'rgba(255,255,255,0.4)',
}

const gridStyle = { stroke: 'rgba(255,255,255,0.06)' }

// ── Stagger children ────────────────────────────────────────────────────────

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
}
const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  return (
    <m.div
      variants={stagger}
      initial="hidden"
      animate="show"
      className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-6"
    >
      {/* Header */}
      <m.div variants={fadeUp}>
        <h1 className="text-xl font-display font-semibold text-text-primary mb-0.5">Analytics</h1>
        <p className="text-xs text-text-muted">Performance metrics and insights</p>
      </m.div>

      {/* KPI Row */}
      <m.div variants={fadeUp} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {pipelineStats.map((stat) => (
          <GlassCard key={stat.label} level="near" className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xxs text-text-ghost font-mono uppercase tracking-wider">
                {stat.label}
              </span>
              <stat.Icon className="w-3.5 h-3.5 text-text-ghost" />
            </div>
            <div className="flex items-end justify-between">
              <span className="text-2xl font-display font-bold text-text-primary">{stat.value}</span>
              <span
                className={cn(
                  'inline-flex items-center gap-0.5 text-xxs font-mono font-semibold',
                  stat.positive ? 'text-status-success' : 'text-status-warning'
                )}
              >
                {stat.positive ? (
                  <TrendingUp className="w-3 h-3" />
                ) : (
                  <TrendingDown className="w-3 h-3" />
                )}
                {stat.change}
              </span>
            </div>
          </GlassCard>
        ))}
      </m.div>

      {/* Charts Row */}
      <m.div variants={fadeUp} className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Health Trend */}
        <GlassCard level="mid" className="p-5">
          <h3 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider mb-4">
            Health Trend (7d)
          </h3>
          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={healthTrend} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                <defs>
                  <linearGradient id="healthGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#00E5C4" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00E5C4" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" {...gridStyle} />
                <XAxis dataKey="day" tick={axisStyle} tickLine={false} axisLine={false} />
                <YAxis domain={[50, 100]} tick={axisStyle} tickLine={false} axisLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area
                  type="monotone"
                  dataKey="avg"
                  stroke="#00E5C4"
                  strokeWidth={2}
                  fill="url(#healthGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Ticket Volume */}
        <GlassCard level="mid" className="p-5">
          <h3 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider mb-4">
            Ticket Volume (7d)
          </h3>
          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ticketVolume} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" {...gridStyle} />
                <XAxis dataKey="day" tick={axisStyle} tickLine={false} axisLine={false} />
                <YAxis tick={axisStyle} tickLine={false} axisLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="P1" stackId="a" fill="#FF5C5C" radius={[0, 0, 0, 0]} />
                <Bar dataKey="P2" stackId="a" fill="#FFB547" />
                <Bar dataKey="P3" stackId="a" fill="#3B9EFF" />
                <Bar dataKey="P4" stackId="a" fill="#5C5C72" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          {/* Legend */}
          <div className="flex items-center gap-4 mt-3">
            {[
              { key: 'P1', color: '#FF5C5C' },
              { key: 'P2', color: '#FFB547' },
              { key: 'P3', color: '#3B9EFF' },
              { key: 'P4', color: '#5C5C72' },
            ].map((l) => (
              <span key={l.key} className="inline-flex items-center gap-1.5 text-xxs text-text-ghost">
                <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: l.color }} />
                {l.key}
              </span>
            ))}
          </div>
        </GlassCard>
      </m.div>

      {/* Bottom Row */}
      <m.div variants={fadeUp} className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Sentiment Pie — 2/5 */}
        <GlassCard level="mid" className="p-5 lg:col-span-2">
          <h3 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider mb-4">
            Call Sentiment Distribution
          </h3>
          <div style={{ height: 220 }} className="relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sentimentDist}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  dataKey="value"
                  paddingAngle={2}
                  strokeWidth={0}
                >
                  {sentimentDist.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null
                    const d = payload[0].payload
                    return (
                      <div className="rounded-lg px-3 py-2 text-xs border bg-[#0A1628] border-white/10 shadow-xl">
                        <p style={{ color: d.color }}>{d.name}</p>
                        <p className="text-text-primary font-mono">{d.value} calls</p>
                      </div>
                    )
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            {/* Center label */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <span className="text-2xl font-display font-bold text-text-primary">{totalCalls}</span>
                <br />
                <span className="text-xxs text-text-ghost">calls</span>
              </div>
            </div>
          </div>
          {/* Legend */}
          <div className="flex flex-wrap gap-3 mt-2 justify-center">
            {sentimentDist.map((d) => (
              <span key={d.name} className="inline-flex items-center gap-1.5 text-xxs text-text-ghost">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                {d.name}
              </span>
            ))}
          </div>
        </GlassCard>

        {/* Agent Performance Table — 3/5 */}
        <GlassCard level="mid" className="p-5 lg:col-span-3">
          <h3 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider mb-4">
            Agent Performance
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="pb-2 text-xxs font-mono font-semibold text-text-ghost uppercase tracking-wider">
                    Agent
                  </th>
                  <th className="pb-2 text-xxs font-mono font-semibold text-text-ghost uppercase tracking-wider">
                    Role
                  </th>
                  <th className="pb-2 text-xxs font-mono font-semibold text-text-ghost uppercase tracking-wider text-right">
                    Tasks
                  </th>
                  <th className="pb-2 text-xxs font-mono font-semibold text-text-ghost uppercase tracking-wider text-right">
                    Avg Time
                  </th>
                  <th className="pb-2 text-xxs font-mono font-semibold text-text-ghost uppercase tracking-wider text-right">
                    Accuracy
                  </th>
                </tr>
              </thead>
              <tbody>
                {agentPerformance.map((agent) => (
                  <tr key={agent.name} className="border-b border-border-subtle/50 last:border-0">
                    <td className="py-2.5">
                      <div className="flex items-center gap-2">
                        <AgentAvatar name={agent.name} tier={agent.tier} size="sm" className="w-5 h-5 text-[9px]" />
                        <span className="text-xs text-text-primary font-medium">{agent.name}</span>
                      </div>
                    </td>
                    <td className="py-2.5 text-xxs text-text-muted">{agent.role}</td>
                    <td className="py-2.5 text-xs text-text-secondary font-mono text-right">{agent.tasks}</td>
                    <td className="py-2.5 text-xs text-text-muted font-mono text-right">{agent.avgTime}</td>
                    <td className={cn('py-2.5 text-xs font-mono font-semibold text-right', accuracyColor(agent.accuracy))}>
                      {agent.accuracy}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      </m.div>
    </m.div>
  )
}
