import { m } from 'framer-motion'
import { Monitor, Wifi, WifiOff, User, LogOut } from 'lucide-react'
import useSettingsStore from '../stores/settingsStore'
import useWebsocketStore from '../stores/websocketStore'
import useAuthStore from '../stores/authStore'
import useDashboardStore from '../stores/dashboardStore'

function Toggle({ checked, onChange, label }) {
  return (
    <button
      onClick={onChange}
      className="relative flex-shrink-0 w-11 h-6 rounded-full transition-colors duration-200"
      style={{ backgroundColor: checked ? 'var(--accent)' : 'var(--bg-active)' }}
      aria-label={label}
      role="switch"
      aria-checked={checked}
    >
      <span
        className="absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform duration-200"
        style={{ transform: checked ? 'translateX(20px)' : 'translateX(0)' }}
      />
    </button>
  )
}

function SettingRow({ label, description, children }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-border-subtle last:border-0">
      <div>
        <p className="text-sm text-text-primary">{label}</p>
        {description && <p className="text-xs text-text-ghost mt-0.5">{description}</p>}
      </div>
      {children}
    </div>
  )
}

function StatusRow({ label, value, color, icon: Icon }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-border-subtle last:border-0">
      <div className="flex items-center gap-2">
        {Icon && <Icon className="w-3.5 h-3.5 text-text-ghost" />}
        <span className="text-xs text-text-ghost">{label}</span>
      </div>
      <span className="text-xs font-mono font-semibold" style={color ? { color } : undefined}>
        {value}
      </span>
    </div>
  )
}

export default function SettingsPage() {
  const reducedMotion = useSettingsStore((s) => s.reducedMotion)
  const toggleReducedMotion = useSettingsStore((s) => s.toggleReducedMotion)
  const wsConnected = useWebsocketStore((s) => s.connected)
  const logout = useAuthStore((s) => s.logout)
  const user = useAuthStore((s) => s.user)
  const stats = useDashboardStore((s) => s.stats)

  const activeAgents = stats?.active_agents ?? stats?.agents_active ?? '—'
  const totalAgents = stats?.total_agents ?? 13

  return (
    <m.div
      data-testid="settings-page"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="w-full max-w-2xl mx-auto space-y-4"
    >
      <h1 className="text-xl font-semibold text-text-primary mb-6">Settings</h1>

      {/* Preferences */}
      <div className="card p-5">
        <h2 className="text-xs text-text-primary font-semibold uppercase tracking-wider mb-2">Preferences</h2>
        <SettingRow label="Reduce Motion" description="Disable animations for accessibility">
          <Toggle
            checked={reducedMotion}
            onChange={toggleReducedMotion}
            label="Toggle reduced motion"
          />
        </SettingRow>
      </div>

      {/* System Status */}
      <div className="card p-5">
        <h2 className="text-xs text-text-primary font-semibold uppercase tracking-wider mb-2">System Status</h2>
        <StatusRow
          label="WebSocket"
          icon={wsConnected ? Wifi : WifiOff}
          value={wsConnected ? 'Connected' : 'Disconnected'}
          color={wsConnected ? '#00E5A0' : '#FF5C5C'}
        />
        <StatusRow
          label="Agents"
          icon={Monitor}
          value={`${activeAgents} active / ${totalAgents} total`}
        />
      </div>

      {/* Account */}
      <div className="card p-5">
        <h2 className="text-xs text-text-primary font-semibold uppercase tracking-wider mb-2">Account</h2>
        <div className="flex items-center justify-between py-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center">
              <User className="w-4 h-4 text-accent" />
            </div>
            <div>
              <p className="text-sm text-text-primary font-medium">
                {user?.name || user?.email || 'Demo User'}
              </p>
              <p className="text-xs text-text-ghost font-mono">
                {user?.email || 'demo@hivepro.com'}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono text-status-danger/70 hover:text-status-danger hover:bg-status-danger/10 border border-transparent hover:border-status-danger/20 transition-all"
          >
            <LogOut className="w-3 h-3" />
            Sign Out
          </button>
        </div>
      </div>
    </m.div>
  )
}
