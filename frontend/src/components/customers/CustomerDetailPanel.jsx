import { motion, AnimatePresence } from 'framer-motion'
import { X, ChevronDown, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import HealthScoreBadge from './HealthScoreBadge'
import { formatDate } from '../../utils/formatters'

function Section({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border-b" style={{ borderColor: 'var(--border)' }}>
      <button
        className="flex items-center justify-between w-full px-5 py-3 text-sm font-medium cursor-pointer"
        style={{ color: 'var(--text-primary)' }}
        onClick={() => setOpen(prev => !prev)}
      >
        {title}
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function CustomerDetailPanel({ customer, onClose }) {
  if (!customer) return null

  return (
    <AnimatePresence>
      {/* Backdrop */}
      <motion.div
        key="backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-40"
        style={{ background: 'rgba(0, 0, 0, 0.4)' }}
        onClick={onClose}
      />
      {/* Panel */}
      <motion.div
        key="panel"
        initial={{ x: 400, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 400, opacity: 0 }}
        transition={{ duration: 0.25, ease: 'easeOut' }}
        className="fixed top-0 right-0 h-screen w-[420px] z-50 overflow-y-auto shadow-xl"
        style={{
          background: 'var(--bg-paper)',
          borderLeft: '1px solid var(--border)',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b" style={{ borderColor: 'var(--border)' }}>
          <div>
            <h2 className="text-base font-medium" style={{ color: 'var(--text-primary)' }}>{customer.name}</h2>
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Customer Overview</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded cursor-pointer transition-colors duration-150"
            style={{ color: 'var(--text-muted)' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Sections */}
        <Section title="Overview">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <span className="text-[11px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Health Score</span>
              <div className="mt-1"><HealthScoreBadge score={customer.health_score} /></div>
            </div>
            <div>
              <span className="text-[11px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>ARR</span>
              <p className="text-sm font-mono mt-1" style={{ color: 'var(--text-primary)' }}>
                ${(customer.arr / 1000).toFixed(0)}K
              </p>
            </div>
            <div>
              <span className="text-[11px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>CSM Owner</span>
              <p className="text-sm mt-1" style={{ color: 'var(--text-primary)' }}>{customer.csm_owner}</p>
            </div>
            <div>
              <span className="text-[11px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Open Tickets</span>
              <p className="text-sm mt-1" style={{ color: 'var(--text-primary)' }}>{customer.open_tickets}</p>
            </div>
          </div>
        </Section>

        <Section title="Recent Meetings" defaultOpen={false}>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            Last meeting: {customer.last_meeting ? formatDate(customer.last_meeting) : 'No meetings recorded'}
          </p>
        </Section>

        <Section title="Open Tickets" defaultOpen={false}>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            {customer.open_tickets} open tickets
          </p>
        </Section>

        <Section title="HubSpot Deal" defaultOpen={false}>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            Segment: {customer.segment || 'Enterprise'}
          </p>
        </Section>
      </motion.div>
    </AnimatePresence>
  )
}
