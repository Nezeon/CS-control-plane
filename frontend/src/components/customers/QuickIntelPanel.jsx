import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import HealthRing from '../shared/HealthRing'

export default function QuickIntelPanel({ customer }) {
  const navigate = useNavigate()

  return (
    <AnimatePresence>
      {customer && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.15 }}
          className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 hidden lg:block"
        >
          <div className="card-elevated flex items-center gap-4 px-5 py-3 shadow-lg border border-border-strong">
            <HealthRing score={customer.health_score} size="sm" />
            <div>
              <p className="text-sm font-medium text-text-primary">{customer.company_name || customer.name}</p>
              <p className="text-xxs text-text-muted">
                {customer.open_tickets ?? 0} tickets · {customer.recent_calls ?? 0} calls
                {customer.industry ? ` · ${customer.industry}` : ''}
              </p>
            </div>
            <button
              onClick={() => navigate(`/customers/${customer.id}`)}
              className="ml-4 px-3 py-1.5 rounded-md bg-accent text-white text-xs font-medium hover:bg-accent-hover transition-colors"
            >
              View
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
