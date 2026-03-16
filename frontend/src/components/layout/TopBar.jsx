import { useState, useRef, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Search, Bell, ChevronRight, LogOut, Settings } from 'lucide-react'
import { cn } from '../../utils/cn'
import useAuthStore from '../../stores/authStore'
import useAlertStore from '../../stores/alertStore'
import { getInitials } from '../../utils/formatters'

const ROUTE_NAMES = {
  '/': 'Dashboard',
  '/customers': 'Customers',
  '/agents': 'AI Agents',
  '/conversations': 'Conversations',
  '/pipelines': 'Pipelines',
  '/knowledge': 'Knowledge',
  '/tickets': 'Tickets',
  '/calls': 'Calls',
  '/alerts': 'Alerts',
  '/workflows': 'Workflows',
  '/analytics': 'Analytics',
  '/settings': 'Settings',
}

function getBreadcrumbs(pathname) {
  if (pathname === '/') return [{ label: 'Dashboard', path: '/' }]

  const parts = pathname.split('/').filter(Boolean)
  const crumbs = []

  if (parts[0]) {
    const basePath = `/${parts[0]}`
    crumbs.push({ label: ROUTE_NAMES[basePath] || parts[0], path: basePath })
  }

  if (parts[1]) {
    crumbs.push({ label: parts[1], path: pathname })
  }

  return crumbs
}

export default function TopBar({ onOpenCommandPalette }) {
  const location = useLocation()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const alerts = useAlertStore((s) => s.alerts)
  const openAlertCount = (alerts || []).filter((a) => a.status === 'open').length
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const menuRef = useRef(null)

  const breadcrumbs = getBreadcrumbs(location.pathname)

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = () => {
    setUserMenuOpen(false)
    logout()
    navigate('/login')
  }

  return (
    <header
      data-testid="top-bar"
      className="sticky top-0 z-20 h-14 flex items-center justify-between px-6 bg-bg/80 backdrop-blur-sm border-b border-border"
    >
      {/* Left: Breadcrumbs */}
      <nav className="flex items-center gap-1.5" aria-label="Breadcrumb">
        {breadcrumbs.map((crumb, i) => (
          <div key={crumb.path} className="flex items-center gap-1.5">
            {i > 0 && <ChevronRight className="w-3.5 h-3.5 text-text-ghost" />}
            {i < breadcrumbs.length - 1 ? (
              <Link
                to={crumb.path}
                className="text-sm text-text-muted hover:text-text-secondary transition-colors"
              >
                {crumb.label}
              </Link>
            ) : (
              <span className="text-sm font-medium text-text-primary">{crumb.label}</span>
            )}
          </div>
        ))}
      </nav>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Search trigger */}
        <button
          onClick={onOpenCommandPalette}
          data-testid="search-trigger"
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border text-text-muted hover:text-text-secondary hover:border-border-strong transition-colors"
        >
          <Search className="w-3.5 h-3.5" />
          <span className="text-xs hidden sm:inline">Search</span>
          <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded bg-bg-active border border-border text-xxs font-mono text-text-ghost">
            Ctrl+K
          </kbd>
        </button>

        {/* Notifications */}
        <button
          className="relative p-2 rounded-lg text-text-muted hover:text-text-secondary hover:bg-bg-active transition-colors"
          aria-label={`Notifications${openAlertCount > 0 ? ` (${openAlertCount} new)` : ''}`}
        >
          <Bell className="w-4 h-4" />
          {openAlertCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-status-danger" />
          )}
        </button>

        {/* User avatar */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 p-1 rounded-lg hover:bg-bg-active transition-colors"
            aria-label="User menu"
          >
            <div className="w-7 h-7 rounded-full bg-accent flex items-center justify-center text-white text-xxs font-semibold">
              {getInitials(user?.full_name)}
            </div>
          </button>

          {userMenuOpen && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-bg-elevated border border-border-strong rounded-lg overflow-hidden shadow-xl">
              <div className="px-3 py-2 border-b border-border">
                <p className="text-sm font-medium text-text-primary truncate">{user?.full_name || 'User'}</p>
                <p className="text-xxs text-text-muted truncate">{user?.email}</p>
              </div>
              <div className="py-1">
                <button
                  onClick={() => { setUserMenuOpen(false); navigate('/settings') }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-text-secondary hover:bg-bg-active transition-colors"
                >
                  <Settings className="w-3.5 h-3.5" />
                  Settings
                </button>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-status-danger hover:bg-bg-active transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
