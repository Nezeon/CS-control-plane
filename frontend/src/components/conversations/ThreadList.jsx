import { useMemo } from 'react'
import { Search } from 'lucide-react'
import { cn } from '../../utils/cn'
import GlassCard from '../shared/GlassCard'
import PillFilter from '../shared/PillFilter'
import ThreadPreview from './ThreadPreview'

const filterOptions = [
  { value: 'all', label: 'All' },
  { value: 'tickets', label: 'Tickets' },
  { value: 'calls', label: 'Calls' },
  { value: 'escalation', label: 'Escalation' },
]

export default function ThreadList({ threads, selectedThread, filter, onFilterChange, onSelectThread }) {
  const filteredThreads = useMemo(() => {
    if (!threads) return []
    if (filter === 'all') return threads
    // Filter threads by priority mapping (approximation from event type)
    return threads.filter((t) => {
      if (filter === 'escalation') return t.priority === 'critical'
      if (filter === 'tickets') return t.event_type === 'jira_ticket_created'
      if (filter === 'calls') return t.event_type === 'fathom_call_processed' || t.event_type === 'qbr_scheduled'
      return true
    })
  }, [threads, filter])

  return (
    <GlassCard level="near" className="flex flex-col h-full p-0 overflow-hidden">
      {/* Header */}
      <div className="p-4 pb-3 border-b border-border-subtle">
        <div className="flex items-center gap-2 mb-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-ghost" />
            <input
              type="text"
              placeholder="Search conversations..."
              className={cn(
                'w-full pl-9 pr-3 py-2 rounded-lg text-xs',
                'bg-bg-subtle border border-border-subtle',
                'text-text-secondary placeholder:text-text-ghost',
                'focus:outline-none focus:border-accent/30',
                'transition-colors'
              )}
            />
          </div>
        </div>
        <PillFilter options={filterOptions} value={filter} onChange={onFilterChange} />
      </div>

      {/* Thread list */}
      <div className="flex-1 overflow-y-auto">
        {filteredThreads.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <p className="text-xs text-text-ghost">No conversations found</p>
          </div>
        ) : (
          filteredThreads.map((thread) => (
            <ThreadPreview
              key={thread.thread_id}
              thread={thread}
              selected={selectedThread?.thread_id === thread.thread_id}
              onClick={() => onSelectThread(thread)}
            />
          ))
        )}
      </div>
    </GlassCard>
  )
}
