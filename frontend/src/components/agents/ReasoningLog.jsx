import { useRef, useEffect } from 'react'
import { AnimatePresence, m } from 'framer-motion'
import LoadingSkeleton from '../shared/LoadingSkeleton'
import StatusIndicator from '../shared/StatusIndicator'
import { formatTime, getEventTypeColor } from '../../utils/formatters'

export default function ReasoningLog({ logs = [], isLoading = false }) {
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs.length])

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2 p-4">
        <LoadingSkeleton variant="text" count={6} />
      </div>
    )
  }

  if (!logs.length) {
    return (
      <div className="flex items-center justify-center h-full text-text-ghost font-mono text-sm opacity-50">
        <span className="mr-2">▶</span> Awaiting agent activity…
      </div>
    )
  }

  return (
    <div
      data-testid="reasoning-log"
      ref={scrollRef}
      className="h-full overflow-y-auto scrollbar-thin font-mono text-xs leading-relaxed bg-bg"
    >
      <div className="p-3 flex flex-col gap-1">
        <AnimatePresence initial={false}>
          {logs.map((log, i) => (
            <m.div
              key={log.id || i}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2, delay: i * 0.02 }}
              className="flex items-start gap-3 py-1.5 border-b border-border-subtle last:border-0"
            >
              <span className="text-text-ghost shrink-0 w-12 tabular-nums">
                {formatTime(log.started_at || log.created_at)}
              </span>

              <div className="shrink-0 mt-0.5">
                <StatusIndicator status={log.status || 'idle'} size="sm" />
              </div>

              <div className="flex-1 min-w-0">
                {log.trigger_event && (
                  <span
                    className="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider mr-2"
                    style={{
                      backgroundColor: `${getEventTypeColor(log.trigger_event)}15`,
                      color: getEventTypeColor(log.trigger_event),
                    }}
                  >
                    {log.trigger_event.replace(/_/g, ' ')}
                  </span>
                )}

                <span className="text-text-secondary">
                  {log.input_summary || log.description || 'Processing…'}
                </span>

                {log.output_summary && (
                  <div className="text-accent mt-0.5 truncate opacity-70">
                    → {log.output_summary}
                  </div>
                )}
              </div>

              {log.duration_ms != null && (
                <span className="shrink-0 text-text-ghost tabular-nums">
                  {log.duration_ms < 1000
                    ? `${log.duration_ms}ms`
                    : `${(log.duration_ms / 1000).toFixed(1)}s`}
                </span>
              )}
            </m.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
