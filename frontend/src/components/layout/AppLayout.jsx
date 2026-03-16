import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Activity } from 'lucide-react'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/pipeline', label: 'Pipeline', icon: Activity },
]

export default function AppLayout({ children }) {
  return (
    <div className="min-h-screen">
      {/* Top Navigation */}
      <nav className="glass-near sticky top-0 z-50 border-b border-white/[0.04]" style={{ borderRadius: 0 }}>
        <div className="max-w-[1400px] mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <span className="font-display text-base font-bold text-text-primary tracking-tight">
              CS Control Plane
            </span>
            <div className="flex items-center gap-1">
              {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                      isActive
                        ? 'bg-[var(--accent)]/10 text-[var(--accent)]'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                    }`
                  }
                >
                  <Icon size={15} />
                  {label}
                </NavLink>
              ))}
            </div>
          </div>
          <span className="text-xs text-[var(--text-ghost)] font-mono">Phase 1</span>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-[1400px] mx-auto">
        {children}
      </main>
    </div>
  )
}
