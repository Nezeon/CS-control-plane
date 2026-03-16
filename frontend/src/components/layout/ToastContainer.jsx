import { AnimatePresence, m } from 'framer-motion'
import { X, CheckCircle, AlertTriangle, Info, XCircle } from 'lucide-react'
import useToastStore from '../../stores/toastStore'

const typeConfig = {
  success: { icon: CheckCircle, accent: 'border-l-status-success', iconClass: 'text-status-success' },
  error: { icon: XCircle, accent: 'border-l-status-danger', iconClass: 'text-status-danger' },
  warning: { icon: AlertTriangle, accent: 'border-l-status-warning', iconClass: 'text-status-warning' },
  info: { icon: Info, accent: 'border-l-accent', iconClass: 'text-accent' },
}

export default function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts)
  const removeToast = useToastStore((s) => s.removeToast)

  return (
    <div className="fixed top-16 right-4 z-[60] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => {
          const config = typeConfig[toast.type] || typeConfig.info
          const Icon = config.icon

          return (
            <m.div
              key={toast.id}
              initial={{ opacity: 0, x: 80, scale: 0.96 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 80, scale: 0.96 }}
              transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
              className={`pointer-events-auto w-80 bg-bg-elevated border border-border-strong rounded-lg overflow-hidden shadow-xl border-l-[3px] ${config.accent}`}
            >
              <div className="flex items-start gap-3 p-3">
                <Icon className={`w-4 h-4 flex-shrink-0 mt-0.5 ${config.iconClass}`} />
                <div className="flex-1 min-w-0">
                  {toast.title && (
                    <p className="text-sm font-medium text-text-primary">{toast.title}</p>
                  )}
                  {toast.message && (
                    <p className="text-xs text-text-muted mt-0.5">{toast.message}</p>
                  )}
                </div>
                <button
                  onClick={() => removeToast(toast.id)}
                  className="flex-shrink-0 p-1 rounded hover:bg-bg-active transition-colors"
                >
                  <X className="w-3.5 h-3.5 text-text-ghost" />
                </button>
              </div>
            </m.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}
