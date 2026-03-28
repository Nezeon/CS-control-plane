import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, AlertTriangle, Bell } from 'lucide-react'
import api from '../../services/api'
import { formatRelativeTime } from '../../utils/formatters'

const SEVERITY_COLORS = {
  critical: 'var(--status-danger)',
  high: 'var(--status-warning)',
  medium: 'var(--sky)',
  low: 'var(--text-muted)',
}

export default function AlertsDrawer({ open, onClose }) {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    api.get('/alerts', { params: { status: 'open', limit: 50 } })
      .then(({ data }) => setAlerts(data?.alerts || []))
      .catch(() => setAlerts([]))
      .finally(() => setLoading(false))
  }, [open])

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            key="alerts-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40"
            style={{ background: 'rgba(0, 0, 0, 0.4)' }}
            onClick={onClose}
          />
          {/* Drawer */}
          <motion.div
            key="alerts-panel"
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="fixed top-0 right-0 h-screen w-[400px] z-50 flex flex-col shadow-xl"
            style={{ background: 'var(--bg-paper)', borderLeft: '1px solid var(--border)' }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b flex-shrink-0" style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-2">
                <Bell size={16} style={{ color: 'var(--primary)' }} />
                <h2 className="text-base font-medium" style={{ color: 'var(--text-primary)' }}>
                  Active Alerts
                </h2>
                {alerts.length > 0 && (
                  <span
                    className="text-[10px] font-medium px-1.5 py-0.5 rounded-full"
                    style={{ background: 'var(--status-danger)', color: '#FFFFFF' }}
                  >
                    {alerts.length}
                  </span>
                )}
              </div>
              <button
                onClick={onClose}
                className="p-1 rounded cursor-pointer transition-colors duration-150"
                style={{ color: 'var(--text-muted)' }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Alert list */}
            <div className="flex-1 overflow-y-auto">
              {loading && (
                <div className="p-5 text-sm" style={{ color: 'var(--text-muted)' }}>Loading alerts...</div>
              )}
              {!loading && alerts.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <AlertTriangle size={24} style={{ color: 'var(--text-ghost)' }} />
                  <p className="text-sm mt-3" style={{ color: 'var(--text-muted)' }}>No active alerts</p>
                </div>
              )}
              {alerts.map(alert => (
                <div
                  key={alert.id}
                  className="px-5 py-4 border-b"
                  style={{ borderColor: 'var(--border)' }}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className="w-1 flex-shrink-0 self-stretch rounded-full"
                      style={{ background: SEVERITY_COLORS[alert.severity] || SEVERITY_COLORS.medium }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                          {alert.title}
                        </span>
                        {alert.severity && (
                          <span
                            className="text-[10px] uppercase font-medium px-1.5 py-0.5 rounded"
                            style={{
                              color: SEVERITY_COLORS[alert.severity] || 'var(--text-muted)',
                              background: 'var(--bg-hover)',
                            }}
                          >
                            {alert.severity}
                          </span>
                        )}
                      </div>
                      {alert.description && (
                        <p className="text-xs leading-relaxed mb-1" style={{ color: 'var(--text-secondary)' }}>
                          {alert.description}
                        </p>
                      )}
                      <div className="flex items-center gap-2">
                        {alert.customer?.name && (
                          <span className="text-[11px] font-medium" style={{ color: 'var(--primary)' }}>
                            {alert.customer.name}
                          </span>
                        )}
                        <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                          {formatRelativeTime(alert.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
