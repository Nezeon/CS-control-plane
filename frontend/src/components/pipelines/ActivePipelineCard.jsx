import { m } from 'framer-motion'
import { cn } from '../../utils/cn'
import { formatRelativeTime } from '../../utils/formatters'
import GlassCard from '../shared/GlassCard'
import AgentAvatar from '../shared/AgentAvatar'
import TierBadge from '../shared/TierBadge'
import { PIPELINE_STAGES } from '../../data/pipelines'

const stageLabels = {
  perceive: 'Perceive',
  retrieve: 'Retrieve',
  think: 'Think',
  act: 'Act',
  reflect: 'Reflect',
  quality_gate: 'QA Gate',
  finalize: 'Finalize',
}

function getStageStatus(rounds, stageType) {
  const round = rounds?.find((r) => (r.stage_type || r.stage) === stageType)
  return round?.status || 'pending'
}

export default function ActivePipelineCard({ execution }) {
  const totalTokens = execution.total_tokens || 0

  return (
    <GlassCard level="near" className="p-4">
      <div className="flex items-start gap-4">
        {/* Left: agent info */}
        <div className="flex items-center gap-3 shrink-0 w-48">
          <AgentAvatar
            name={execution.agent_name}
            tier={execution.tier || execution.agent_tier}
            size="md"
            status="processing"
          />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-text-primary truncate">{execution.agent_name}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <TierBadge tier={execution.tier || execution.agent_tier} />
              <span className="text-xxs text-text-ghost truncate">{execution.customer_name}</span>
            </div>
          </div>
        </div>

        {/* Center: stage timeline */}
        <div className="flex-1 flex items-center gap-1 min-w-0 pt-1">
          {PIPELINE_STAGES.map((stage, i) => {
            const status = getStageStatus(execution.rounds, stage)
            const isCompleted = status === 'completed'
            const isRunning = status === 'running'
            const isPending = status === 'pending'

            return (
              <div key={stage} className="flex items-center flex-1 min-w-0">
                {/* Dot */}
                <div className="flex flex-col items-center gap-1">
                  <div className="relative">
                    <div
                      className={cn(
                        'w-3 h-3 rounded-full border-2 transition-colors',
                        isCompleted && 'bg-teal border-teal',
                        isRunning && 'bg-accent border-accent animate-pulse-glow',
                        isPending && 'bg-transparent border-text-ghost/40'
                      )}
                    />
                    {isRunning && (
                      <m.div
                        className="absolute inset-0 rounded-full border-2 border-accent"
                        animate={{ scale: [1, 1.8], opacity: [0.6, 0] }}
                        transition={{ duration: 1.2, repeat: Infinity }}
                      />
                    )}
                  </div>
                  <span
                    className={cn(
                      'text-[9px] font-mono leading-none whitespace-nowrap',
                      isCompleted && 'text-teal',
                      isRunning && 'text-accent',
                      isPending && 'text-text-ghost'
                    )}
                  >
                    {stageLabels[stage]}
                  </span>
                </div>

                {/* Connector line */}
                {i < PIPELINE_STAGES.length - 1 && (
                  <div
                    className={cn(
                      'flex-1 h-px mx-1',
                      isCompleted ? 'bg-teal/40' : 'bg-border-subtle'
                    )}
                  />
                )}
              </div>
            )
          })}
        </div>

        {/* Right: meta */}
        <div className="shrink-0 text-right">
          <p className="text-xxs text-text-ghost font-mono">{formatRelativeTime(execution.started_at)}</p>
          <p className="text-xxs text-text-muted font-mono mt-0.5">{totalTokens.toLocaleString()} tokens</p>
        </div>
      </div>

      {/* Trigger description */}
      <div className="flex items-center gap-2 mt-3 pl-[204px]">
        <p className="text-xs text-text-muted truncate">
          {execution.trigger || execution.event_type}
        </p>
        {(execution.trigger || execution.event_type || '').startsWith('user_chat_') && (
          <span className="shrink-0 text-xxs px-1.5 py-0.5 rounded bg-accent/10 text-accent border border-accent/20">
            Chat Query
          </span>
        )}
      </div>
    </GlassCard>
  )
}
