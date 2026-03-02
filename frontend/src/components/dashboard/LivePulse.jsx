import useDashboardStore from '../../stores/dashboardStore'
import EventPulseItem from '../shared/EventPulseItem'
import LoadingSkeleton from '../shared/LoadingSkeleton'

export default function LivePulse() {
  const events = useDashboardStore((s) => s.events)

  if (!events) {
    return (
      <div className="card p-4">
        <LoadingSkeleton variant="text" count={6} />
      </div>
    )
  }

  const displayEvents = events.slice(0, 10)
  const totalCount = events.length

  return (
    <div className="card p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-medium text-text-primary">Live Activity</h2>
        <span className="text-xxs text-text-ghost font-mono tabular-nums">{totalCount} events</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-0.5 min-h-0 -mx-1 px-1" style={{ maxHeight: 320 }}>
        {displayEvents.length === 0 ? (
          <p className="text-xs text-text-ghost py-8 text-center">Waiting for events...</p>
        ) : (
          displayEvents.map((event, i) => (
            <EventPulseItem key={event.id || i} event={event} isNew={i === 0} />
          ))
        )}
      </div>
    </div>
  )
}
