import { useEffect, useState, useMemo } from 'react'
import { m } from 'framer-motion'
import { Activity, CheckCircle2, Zap } from 'lucide-react'
import usePipelineStore from '../stores/pipelineStore'
import ActivePipelineCard from '../components/pipelines/ActivePipelineCard'
import CompletedPipelineCard from '../components/pipelines/CompletedPipelineCard'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'

export default function PipelinesPage() {
  const { executions, activeExecutions, isLoading, fetchAll } = usePipelineStore()
  const [selectedExecution, setSelectedExecution] = useState(null)

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const completedExecutions = useMemo(
    () => executions.filter((e) => e.status === 'completed' || e.status === 'failed'),
    [executions]
  )

  const totalTokens = useMemo(
    () => executions.reduce((sum, e) => sum + (e.total_tokens || 0), 0),
    [executions]
  )

  if (isLoading && !executions.length && !activeExecutions.length) {
    return (
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-6">
        <div>
          <h1 className="text-xl font-display font-semibold text-text-primary mb-2">Pipelines</h1>
        </div>
        <LoadingSkeleton variant="card" count={4} />
      </div>
    )
  }

  return (
    <m.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-6"
    >
      {/* Header */}
      <div>
        <h1 className="text-xl font-display font-semibold text-text-primary mb-2">Pipelines</h1>
        <div className="flex items-center gap-5">
          <span className="inline-flex items-center gap-1.5 text-xs text-text-muted">
            <Activity className="w-3.5 h-3.5 text-accent" />
            <span className="text-accent font-semibold">{activeExecutions.length}</span> active
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs text-text-muted">
            <CheckCircle2 className="w-3.5 h-3.5 text-teal" />
            <span className="text-teal font-semibold">{completedExecutions.length}</span> completed
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs text-text-muted">
            <Zap className="w-3.5 h-3.5 text-status-warning" />
            <span className="text-status-warning font-semibold">{totalTokens.toLocaleString()}</span> tokens
          </span>
        </div>
      </div>

      {/* Active Now */}
      {activeExecutions.length > 0 && (
        <section>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-accent animate-pulse-subtle" />
            <h3 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider">
              Active Now
            </h3>
          </div>
          <div className="space-y-3">
            {activeExecutions.map((exec) => (
              <ActivePipelineCard key={exec.execution_id} execution={exec} />
            ))}
          </div>
        </section>
      )}

      {/* Recent Completions */}
      <section>
        <h3 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-wider mb-3">
          Recent Completions
        </h3>
        <div className="space-y-2">
          {completedExecutions.map((exec) => (
            <CompletedPipelineCard
              key={exec.execution_id}
              execution={exec}
              expanded={selectedExecution === exec.execution_id}
              onToggle={() =>
                setSelectedExecution((s) =>
                  s === exec.execution_id ? null : exec.execution_id
                )
              }
            />
          ))}
        </div>
        {completedExecutions.length === 0 && (
          <div className="text-center py-12">
            <p className="text-xs text-text-ghost">No completed pipelines yet</p>
          </div>
        )}
      </section>
    </m.div>
  )
}
