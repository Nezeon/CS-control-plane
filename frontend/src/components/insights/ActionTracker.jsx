import { CheckCircle2 } from 'lucide-react'
import LoadingSkeleton from '../shared/LoadingSkeleton'

const EMPTY_ARRAY = []

function StatPill({ label, count, color }) {
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-bg-active border border-border-subtle">
      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
      <span className="text-[10px] font-mono text-text-ghost uppercase">{label}</span>
      <span className="text-sm font-bold tabular-nums ml-auto" style={{ color }}>{count}</span>
    </div>
  )
}

function ActionItemRow({ item, onToggle }) {
  const isCompleted = item.status === 'completed'
  const isOverdue = item.status === 'overdue' || (item.status === 'pending' && item.deadline && new Date(item.deadline) < new Date())

  return (
    <label className="flex items-start gap-2 py-1.5 cursor-pointer group border-b border-border-subtle last:border-0">
      <input
        type="checkbox"
        checked={isCompleted}
        onChange={() => onToggle?.(item.id, isCompleted ? 'pending' : 'completed')}
        className="mt-0.5 accent-accent shrink-0"
      />
      <div className="flex-1 min-w-0">
        <div className={`text-[11px] font-mono truncate ${isCompleted ? 'text-text-ghost line-through' : isOverdue ? 'text-status-danger' : 'text-text-secondary'}`}>
          {item.description || item.text || item.title}
        </div>
        {item.customer_name && (
          <div className="text-[9px] text-text-ghost/60 font-mono mt-0.5 truncate">{item.customer_name}</div>
        )}
      </div>
      {isOverdue && !isCompleted && (
        <span className="shrink-0 w-1.5 h-1.5 rounded-full bg-status-danger animate-pulse mt-1" />
      )}
    </label>
  )
}

export default function ActionTracker({
  actionItems = EMPTY_ARRAY,
  summary = { pending: 0, overdue: 0, completed: 0 },
  isLoading = false,
  onToggleAction,
}) {
  if (isLoading) {
    return (
      <div className="card p-4 w-[260px]">
        <LoadingSkeleton variant="text" count={6} />
      </div>
    )
  }

  const pendingItems = actionItems.filter((i) => i.status !== 'completed').slice(0, 10)
  const hasItems = pendingItems.length > 0

  return (
    <div className="card w-[260px] flex flex-col max-h-[calc(100vh-240px)]" data-testid="action-tracker">
      {/* Header */}
      <div className="px-4 pt-4 pb-2">
        <h3 className="text-xs text-text-primary font-semibold uppercase tracking-widest">
          Action Tracker
        </h3>
      </div>

      {/* Stats */}
      <div className="px-4 pb-3 space-y-1.5">
        <StatPill label="Pending" count={summary.pending} color="#FFB547" />
        <StatPill label="Overdue" count={summary.overdue} color="#FF5C5C" />
        <StatPill label="Done" count={summary.completed} color="#00E5A0" />
      </div>

      {/* Divider */}
      <div className="border-t border-border-subtle" />

      {/* Items */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-2">
        {hasItems ? (
          pendingItems.map((item, i) => (
            <ActionItemRow key={item.id || i} item={item} onToggle={onToggleAction} />
          ))
        ) : (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <CheckCircle2 className="w-5 h-5 text-status-success/40 mb-2" />
            <span className="text-text-ghost font-mono text-[10px]">All caught up!</span>
          </div>
        )}
      </div>

      {/* View all */}
      {actionItems.length > 10 && (
        <div className="px-4 py-2 border-t border-border-subtle">
          <span className="block text-center text-[10px] font-mono text-text-ghost/60">
            +{actionItems.length - 10} more items
          </span>
        </div>
      )}
    </div>
  )
}
