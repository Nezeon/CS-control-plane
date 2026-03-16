import { useState, useEffect, useMemo } from 'react'
import { m } from 'framer-motion'
import {
  GitBranch,
  Activity,
  CheckCircle2,
  Zap,
  ArrowDown,
} from 'lucide-react'
import { cn } from '../utils/cn'
import useWorkflowStore from '../stores/workflowStore'
import GlassCard from '../components/shared/GlassCard'
import StatusPill from '../components/shared/StatusPill'
import TabBar from '../components/shared/TabBar'
import AgentAvatar from '../components/shared/AgentAvatar'
import { formatRelativeTime, getLaneColor } from '../utils/formatters'

const AGENT_TIERS = {
  cso_orchestrator: 1,
  support_lead: 2,
  value_lead: 2,
  delivery_lead: 2,
  triage_agent: 3,
  troubleshooter_agent: 3,
  escalation_agent: 3,
  health_monitor_agent: 3,
  fathom_agent: 3,
  qbr_agent: 3,
  sow_agent: 3,
  deployment_intel_agent: 3,
  customer_memory: 4,
}

const tabs = [
  { key: 'definitions', label: 'Definitions', icon: GitBranch },
  { key: 'active', label: 'Active Instances', icon: Activity },
]

// ── Workflow Definition Card ────────────────────────────────────────────────

function WorkflowDefCard({ workflow }) {
  const laneColor = getLaneColor(workflow.lane)

  return (
    <GlassCard level="mid" className="p-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <h3 className="text-sm font-display font-semibold text-text-primary">
          {workflow.display_name}
        </h3>
        <span
          className="px-2 py-0.5 rounded-full text-xxs font-mono font-semibold uppercase tracking-wider"
          style={{ backgroundColor: laneColor + '15', color: laneColor }}
        >
          {workflow.lane}
        </span>
      </div>
      <p className="text-xs text-text-secondary leading-relaxed mb-4">{workflow.description}</p>

      {/* Steps timeline */}
      <div className="space-y-0 mb-4">
        {workflow.steps.map((step, i) => {
          const tier = AGENT_TIERS[step.agent] || 3
          const isLast = i === workflow.steps.length - 1

          return (
            <div key={step.step} className="flex items-start gap-3">
              {/* Vertical timeline */}
              <div className="flex flex-col items-center">
                <div
                  className="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-mono font-bold border-2 shrink-0"
                  style={{ borderColor: laneColor, color: laneColor }}
                >
                  {step.step}
                </div>
                {!isLast && (
                  <div className="w-px flex-1 min-h-[16px] bg-border-subtle" />
                )}
              </div>

              {/* Step content */}
              <div className="pb-3 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <AgentAvatar name={step.agent_name} tier={tier} size="sm" className="w-4 h-4 text-[8px]" />
                  <span className="text-xs font-medium text-text-primary truncate">
                    {step.agent_name}
                  </span>
                </div>
                <p className="text-xxs text-text-muted">{step.description}</p>
                {step.condition && (
                  <span className="inline-block mt-1 px-1.5 py-0.5 rounded text-xxs font-mono bg-bg-active text-text-ghost border border-border-subtle">
                    {step.condition}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-border-subtle">
        <div className="flex flex-wrap gap-1">
          {workflow.trigger_events.map((evt) => (
            <span
              key={evt}
              className="px-1.5 py-0.5 rounded text-xxs font-mono bg-accent/10 text-accent border border-accent/10"
            >
              {evt}
            </span>
          ))}
        </div>
        <span className="ml-auto text-xxs text-text-ghost font-mono">
          {workflow.total_executions} runs &middot; {workflow.success_rate}% success &middot;{' '}
          {(workflow.avg_duration_ms / 1000).toFixed(0)}s avg
        </span>
      </div>
    </GlassCard>
  )
}

// ── Workflow Instance Card ──────────────────────────────────────────────────

function StepDot({ status }) {
  if (status === 'completed')
    return (
      <div className="w-3 h-3 rounded-full bg-teal flex items-center justify-center">
        <CheckCircle2 className="w-2 h-2 text-bg-void" />
      </div>
    )
  if (status === 'running')
    return <div className="w-3 h-3 rounded-full bg-accent animate-pulse-subtle shadow-[0_0_6px_rgba(99,102,241,0.5)]" />
  if (status === 'skipped')
    return (
      <div className="w-3 h-3 rounded-full border border-text-ghost/30 relative">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-full h-px bg-text-ghost/40 rotate-45" />
        </div>
      </div>
    )
  return <div className="w-3 h-3 rounded-full border border-text-ghost/30" />
}

function WorkflowInstanceCard({ instance, definitions = [] }) {
  const elapsedMs = instance.completed_at
    ? new Date(instance.completed_at) - new Date(instance.started_at)
    : Date.now() - new Date(instance.started_at).getTime()
  const elapsedMin = Math.round(elapsedMs / 60000)

  return (
    <GlassCard level="near" className="p-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h3 className="text-sm font-medium text-text-primary">{instance.display_name}</h3>
          <p className="text-xs text-text-muted mt-0.5">
            {instance.customer_name} &middot; {instance.event_type}
          </p>
        </div>
        <StatusPill status={instance.status} size="sm" />
      </div>

      {/* Step progress */}
      <div className="mb-3">
        <div className="flex items-center gap-1">
          {instance.step_status.map((step, i) => (
            <div key={step.step} className="flex items-center">
              <StepDot status={step.status} />
              {i < instance.step_status.length - 1 && (
                <div
                  className={cn(
                    'h-px w-6 sm:w-10',
                    step.status === 'completed' ? 'bg-teal/40' : 'bg-border-subtle'
                  )}
                />
              )}
            </div>
          ))}
        </div>

        {/* Agent names under dots */}
        <div className="flex items-start gap-1 mt-1.5">
          {instance.step_status.map((step, i) => {
            const def = definitions.find((w) => w.name === instance.workflow_name)
            const stepDef = def?.steps.find((s) => s.step === step.step)
            const name = stepDef?.agent_name || step.agent
            const firstName = name.split(' ')[0]

            return (
              <div key={step.step} className="flex items-center">
                <span
                  className={cn(
                    'text-[9px] font-mono text-center w-3',
                    step.status === 'running'
                      ? 'text-accent'
                      : step.status === 'completed'
                        ? 'text-teal'
                        : 'text-text-ghost'
                  )}
                  title={name}
                >
                  {firstName.slice(0, 3)}
                </span>
                {i < instance.step_status.length - 1 && (
                  <div className="w-6 sm:w-10" />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center gap-4 text-xxs text-text-ghost font-mono">
        <span>Started {formatRelativeTime(instance.started_at)}</span>
        <span>{elapsedMin}m elapsed</span>
        <span>
          Step {instance.current_step}/{instance.total_steps}
        </span>
      </div>
    </GlassCard>
  )
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function WorkflowsPage() {
  const [activeTab, setActiveTab] = useState('definitions')
  const { definitions, instances, fetchAll } = useWorkflowStore()

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const activeCount = useMemo(
    () => instances.filter((i) => i.status === 'running').length,
    [instances]
  )

  return (
    <m.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-5"
    >
      {/* Header */}
      <div>
        <h1 className="text-xl font-display font-semibold text-text-primary mb-1">Workflows</h1>
        <div className="flex items-center gap-5">
          <span className="inline-flex items-center gap-1.5 text-xs text-text-muted">
            <GitBranch className="w-3.5 h-3.5 text-accent" />
            <span className="text-accent font-semibold">{definitions.length}</span> definitions
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs text-text-muted">
            <Activity className="w-3.5 h-3.5 text-teal" />
            <span className="text-teal font-semibold">{activeCount}</span> active
          </span>
        </div>
      </div>

      {/* Tabs */}
      <TabBar tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} className="max-w-sm" />

      {/* Tab content */}
      {activeTab === 'definitions' && (
        <m.div
          key="definitions"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-4"
        >
          {definitions.map((wf) => (
            <WorkflowDefCard key={wf.name} workflow={wf} />
          ))}
        </m.div>
      )}

      {activeTab === 'active' && (
        <m.div
          key="active"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="space-y-3"
        >
          {/* Running */}
          {instances.filter((i) => i.status === 'running').length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 rounded-full bg-accent animate-pulse-subtle" />
                <h3 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider">
                  Running Now
                </h3>
              </div>
              <div className="space-y-2">
                {instances
                  .filter((i) => i.status === 'running')
                  .map((inst) => (
                    <WorkflowInstanceCard key={inst.instance_id} instance={inst} definitions={definitions} />
                  ))}
              </div>
            </section>
          )}

          {/* Completed */}
          {instances.filter((i) => i.status === 'completed').length > 0 && (
            <section>
              <h3 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider mb-3">
                Recently Completed
              </h3>
              <div className="space-y-2">
                {instances
                  .filter((i) => i.status === 'completed')
                  .map((inst) => (
                    <WorkflowInstanceCard key={inst.instance_id} instance={inst} definitions={definitions} />
                  ))}
              </div>
            </section>
          )}

          {instances.length === 0 && (
            <div className="py-16 text-center">
              <p className="text-xs text-text-ghost">No workflow instances</p>
            </div>
          )}
        </m.div>
      )}
    </m.div>
  )
}
