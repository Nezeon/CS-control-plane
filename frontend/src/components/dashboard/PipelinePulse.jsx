import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { m } from 'framer-motion'
import { Workflow, ArrowRight } from 'lucide-react'
import usePipelineStore from '../../stores/pipelineStore'
import AgentAvatar from '../shared/AgentAvatar'
import LoadingSkeleton from '../shared/LoadingSkeleton'

const STAGES = ['perceive', 'retrieve', 'think', 'act', 'reflect', 'quality_gate', 'finalize']

const STAGE_ABBREV = {
  perceive: 'PRC',
  retrieve: 'RTV',
  think: 'THK',
  act: 'ACT',
  reflect: 'RFL',
  quality_gate: 'QGT',
  finalize: 'FIN',
}

function getStageStatus(execution, stage) {
  if (!execution?.rounds?.length) return 'pending'
  const round = execution.rounds.find((r) => r.stage_type === stage)
  if (!round) {
    // Check if current_stage matches
    if (execution.current_stage === stage) return 'running'
    return 'pending'
  }
  return round.status || 'pending'
}

function stageProgress(execution) {
  if (!execution?.rounds?.length) return 0
  const completed = execution.rounds.filter((r) => r.status === 'completed').length
  return Math.round((completed / STAGES.length) * 100)
}

function PipelineTower({ execution }) {
  const navigate = useNavigate()
  const progress = stageProgress(execution)

  return (
    <m.button
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      onClick={() => navigate('/pipelines')}
      className="w-full text-left p-3 rounded-xl bg-bg-active/20 border border-border-subtle hover:border-accent/20 transition-all group"
    >
      {/* Agent + progress header */}
      <div className="flex items-center gap-2.5 mb-3">
        <AgentAvatar
          name={execution.agent_name || execution.agent_id || ''}
          tier={execution.tier || execution.agent_tier || 3}
          size="sm"
          status="active"
          className="shrink-0"
        />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-text-primary truncate group-hover:text-accent transition-colors">
            {execution.agent_name || execution.agent_id}
          </p>
          <p className="text-xxs text-text-ghost font-mono truncate">
            {execution.customer_name || execution.trigger_event || 'Processing...'}
          </p>
        </div>
        <span className="text-xs font-mono font-bold text-accent tabular-nums">{progress}%</span>
      </div>

      {/* Vertical stage tower */}
      <div className="flex items-center gap-1">
        {STAGES.map((stage, i) => {
          const status = getStageStatus(execution, stage)
          const isCompleted = status === 'completed'
          const isRunning = status === 'running'

          return (
            <div key={stage} className="flex-1 flex flex-col items-center gap-1">
              <div
                className={`w-full h-1.5 rounded-full transition-all ${
                  isCompleted
                    ? 'bg-gradient-to-r from-accent to-teal'
                    : isRunning
                    ? 'bg-accent/50 animate-pulse-subtle'
                    : 'bg-bg-active'
                }`}
              />
              <span className="text-[8px] font-mono text-text-ghost leading-none">
                {STAGE_ABBREV[stage]}
              </span>
            </div>
          )
        })}
      </div>
    </m.button>
  )
}

function IdleState() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center py-6 text-center">
      <div className="relative w-16 h-16 flex items-center justify-center">
        <Workflow className="w-6 h-6 text-text-ghost relative z-10" />
        {/* Concentric idle rings */}
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="absolute inset-0 rounded-full border border-accent/10 animate-idle-ring"
            style={{ animationDelay: `${i * 0.8}s` }}
          />
        ))}
      </div>
      <p className="text-xs text-text-muted mt-4">All pipelines idle</p>
      <p className="text-xxs text-text-ghost mt-1">Executions appear here when agents process tasks</p>
    </div>
  )
}

export default function PipelinePulse() {
  const activeExecutions = usePipelineStore((s) => s.activeExecutions)
  const isLoading = usePipelineStore((s) => s.isLoading)
  const fetchActiveExecutions = usePipelineStore((s) => s.fetchActiveExecutions)
  const navigate = useNavigate()

  useEffect(() => {
    fetchActiveExecutions()
  }, [fetchActiveExecutions])

  if (isLoading && !activeExecutions.length) {
    return (
      <div className="glass-near gradient-border rounded-2xl p-5 h-full">
        <div className="flex items-center gap-2 mb-4">
          <Workflow className="w-4 h-4 text-accent" />
          <h2 className="text-sm font-semibold text-text-primary font-display tracking-wide">PIPELINE PULSE</h2>
        </div>
        <LoadingSkeleton variant="text" count={3} />
      </div>
    )
  }

  return (
    <div className="glass-near gradient-border rounded-2xl p-5 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <Workflow className="w-4 h-4 text-accent" />
          <h2 className="text-sm font-semibold text-text-primary font-display tracking-wide">
            PIPELINE PULSE
          </h2>
        </div>
        <button
          onClick={() => navigate('/pipelines')}
          className="flex items-center gap-1 text-xxs text-text-ghost hover:text-accent transition-colors font-mono"
        >
          All <ArrowRight className="w-3 h-3" />
        </button>
      </div>

      {activeExecutions.length === 0 ? (
        <IdleState />
      ) : (
        <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
          {activeExecutions.slice(0, 4).map((exec) => (
            <PipelineTower key={exec.execution_id || exec.id} execution={exec} />
          ))}
          {activeExecutions.length > 4 && (
            <p className="text-xxs text-text-ghost text-center pt-1 font-mono">
              +{activeExecutions.length - 4} more running
            </p>
          )}
        </div>
      )}
    </div>
  )
}
