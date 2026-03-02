import { motion } from 'framer-motion'
import { formatTime, getEventTypeColor } from '../../utils/formatters'

export default function EventPulseItem({ event, isNew = false }) {
  if (!event) return null

  const dotColor = getEventTypeColor(event.event_type)

  return (
    <motion.div
      data-testid="event-pulse-item"
      initial={isNew ? { opacity: 0, y: -8 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-bg-active/50 transition-colors"
    >
      <span
        className="flex-shrink-0 w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: dotColor }}
      />

      <span className="flex-shrink-0 font-mono text-xxs text-text-ghost w-11 tabular-nums">
        {formatTime(event.created_at)}
      </span>

      <span className="flex-1 text-sm text-text-secondary truncate">
        {event.description}
      </span>

      {event.customer_name && (
        <span className="flex-shrink-0 px-2 py-0.5 rounded bg-bg-active font-mono text-xxs text-text-muted">
          {event.customer_name}
        </span>
      )}
    </motion.div>
  )
}
