import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { m } from 'framer-motion'
import { Workflow, ArrowRight } from 'lucide-react'
import usePipelineStore from '../../stores/pipelineStore'
import GlassCard from '../shared/GlassCard'
import AgentAvatar from '../shared/AgentAvatar'
import LoadingSkeleton from '../shared/LoadingSkeleton'

const STAGE_ORDER = ['perceive', 'retrieve', 'think', 'act', 'reflect', 'quality_gate', 'finalize']

function stageProgress(execution) {
  if (!execution?.rounds?.length) return 0
  const completed = execution.rounds.filter((r) => r.status === 'completed').length
  return Math.round((completed / Math.max(STAGE_ORDER.length, 1)) * 100)
}

function PipelineCard({ execution }) {
  const navigate = useNavigate()
  const progress = stageProgress(execution)
  const currentStage = execution.current_stage || execution.rounds?.find((r) => r.status === 'running')?.stage_type || 'perceive'

  return (
    <m.button
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      onClick={() => navigate('/pipelines')}
      className="w-full text-left p-3 rounded-xl bg-bg-active/30 border border-border-subtle hover:border-border transition-all group"
    >
      <div className="flex items-center gap-2.5 mb-2">
        <AgentAvatar
          name={execution.agent_name || execution.agent_id || ''}
          tier={execution.tier || execution.agent_tier || 3}
          size="sm"
          status="active"
          className="flex-shrink-0"
        />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-text-primary truncate group-hover:text-accent transition-colors">
            {execution.agent_name || execution.agent_id}
          </p>
          <p className="text-xxs text-text-ghost font-mono truncate">
            {execution.customer_name || execution.trigger_event || 'Processing...'}
          </p>
        </div>
        <span className="text-xxs font-mono text-accent tabular-nums">{progress}%</span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1 rounded-full bg-bg-subtle overflow-hidden">
        <m.div
          className="h-full rounded-full bg-gradient-to-r from-accent to-teal"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>

      {/* Current stage label */}
      <p className="text-xxs text-text-ghost font-mono mt-1.5">
        Stage: <span className="text-text-muted">{currentStage}</span>
      </p>
    </m.button>
  )
}

export default function ActivePipelines() {
  const activeExecutions = usePipelineStore((s) => s.activeExecutions)
  const isLoading = usePipelineStore((s) => s.isLoading)
  const fetchActiveExecutions = usePipelineStore((s) => s.fetchActiveExecutions)
  const navigate = useNavigate()

  useEffect(() => {
    fetchActiveExecutions()
  }, [fetchActiveExecutions])

  if (isLoading && !activeExecutions.length) {
    return (
      <GlassCard level="near" className="p-5 h-full">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Workflow className="w-3.5 h-3.5 text-accent" />
            <h2 className="text-sm font-semibold text-text-primary font-display">Active Pipelines</h2>
          </div>
        </div>
        <LoadingSkeleton variant="text" count={3} />
      </GlassCard>
    )
  }

  return (
    <GlassCard level="near" className="p-5 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Workflow className="w-3.5 h-3.5 text-accent" />
          <h2 className="text-sm font-semibold text-text-primary font-display">Active Pipelines</h2>
        </div>
        <button
          onClick={() => navigate('/pipelines')}
          className="flex items-center gap-1 text-xxs text-text-ghost hover:text-accent transition-colors"
        >
          View all <ArrowRight className="w-3 h-3" />
        </button>
      </div>

      {activeExecutions.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-8 text-center">
          <div className="w-12 h-12 rounded-xl bg-accent/5 border border-accent/10 flex items-center justify-center mb-4">
            <Workflow className="w-6 h-6 text-text-ghost" />
          </div>
          <p className="text-sm text-text-muted">No active pipelines</p>
          <p className="text-xxs text-text-ghost mt-1.5 max-w-[200px] leading-relaxed">
            Pipeline executions will appear here when agents process tasks
          </p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
          {activeExecutions.slice(0, 5).map((exec) => (
            <PipelineCard key={exec.execution_id || exec.id} execution={exec} />
          ))}
          {activeExecutions.length > 5 && (
            <p className="text-xxs text-text-ghost text-center pt-1 font-mono">
              +{activeExecutions.length - 5} more running
            </p>
          )}
        </div>
      )}
    </GlassCard>
  )
}
