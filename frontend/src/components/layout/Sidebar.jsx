import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard, Users, Brain, Lightbulb, Ticket, BarChart3,
  Settings, PanelLeftClose, PanelLeft, Zap, Menu, X,
} from 'lucide-react'
import { cn } from '../../utils/cn'
import useWebsocketStore from '../../stores/websocketStore'
import useDashboardStore from '../../stores/dashboardStore'
import { formatRelativeTime } from '../../utils/formatters'

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/customers', label: 'Customers', icon: Users },
  { path: '/agents', label: 'Agents', icon: Brain },
  { path: '/insights', label: 'Insights', icon: Lightbulb },
  { path: '/tickets', label: 'Tickets', icon: Ticket },
  { path: '/reports', label: 'Analytics', icon: BarChart3 },
]

const BOTTOM_ITEMS = [
  { path: '/settings', label: 'Settings', icon: Settings },
]

function getActiveRoute(pathname) {
  if (pathname === '/') return '/'
  const match = NAV_ITEMS.find((item) => item.path !== '/' && pathname.startsWith(item.path))
  if (match) return match.path
  const bottomMatch = BOTTOM_ITEMS.find((item) => pathname.startsWith(item.path))
  if (bottomMatch) return bottomMatch.path
  return '/'
}

function NavItem({ item, isActive, collapsed }) {
  const Icon = item.icon
  return (
    <Link
      to={item.path}
      data-testid={`nav-${item.path === '/' ? 'dashboard' : item.path.slice(1)}`}
      className={cn(
        'group relative flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-150',
        isActive
          ? 'bg-accent-subtle text-text-primary'
          : 'text-text-muted hover:text-text-secondary hover:bg-bg-active',
        collapsed && 'justify-center px-0'
      )}
    >
      {isActive && (
        <motion.div
          layoutId="sidebar-indicator"
          className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-accent rounded-r-full"
          transition={{ type: 'spring', stiffness: 500, damping: 35 }}
        />
      )}
      <Icon className={cn('w-[18px] h-[18px] flex-shrink-0', isActive && 'text-accent')} />
      {!collapsed && (
        <span className="text-sm font-medium truncate">{item.label}</span>
      )}
      {collapsed && (
        <div className="absolute left-full ml-2 px-2 py-1 bg-bg-elevated border border-border-strong rounded text-xs text-text-primary whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
          {item.label}
        </div>
      )}
    </Link>
  )
}

export default function Sidebar({ collapsed, onToggle }) {
  const location = useLocation()
  const activeRoute = getActiveRoute(location.pathname)
  const connected = useWebsocketStore((s) => s.connected)
  const events = useDashboardStore((s) => s.events)
  const latestEvents = events.slice(0, 3)
  const [isMobile, setIsMobile] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 768px)')
    setIsMobile(mq.matches)
    const handler = (e) => setIsMobile(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  // Mobile: hamburger trigger
  if (isMobile) {
    return (
      <>
        <button
          onClick={() => setMobileOpen(true)}
          className="fixed top-3 left-3 z-50 p-2 rounded-lg bg-bg-subtle border border-border hover:bg-bg-active transition-colors"
          aria-label="Open navigation"
        >
          <Menu className="w-5 h-5 text-text-secondary" />
        </button>

        <AnimatePresence>
          {mobileOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 bg-black/60"
                onClick={() => setMobileOpen(false)}
              />
              <motion.aside
                initial={{ x: -280 }}
                animate={{ x: 0 }}
                exit={{ x: -280 }}
                transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                className="fixed top-0 left-0 bottom-0 z-50 w-[280px] bg-bg-subtle border-r border-border flex flex-col"
              >
                <SidebarContent
                  activeRoute={activeRoute}
                  collapsed={false}
                  connected={connected}
                  latestEvents={latestEvents}
                  onClose={() => setMobileOpen(false)}
                />
              </motion.aside>
            </>
          )}
        </AnimatePresence>
      </>
    )
  }

  return (
    <aside
      data-testid="sidebar"
      className={cn(
        'fixed top-0 left-0 bottom-0 z-30 bg-bg-subtle border-r border-border flex flex-col transition-[width] duration-200 ease-out-expo',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      <SidebarContent
        activeRoute={activeRoute}
        collapsed={collapsed}
        onToggle={onToggle}
        connected={connected}
        latestEvents={latestEvents}
      />
    </aside>
  )
}

function SidebarContent({ activeRoute, collapsed, onToggle, onClose, connected, latestEvents }) {
  return (
    <>
      {/* Header */}
      <div className={cn(
        'flex items-center h-14 border-b border-border flex-shrink-0',
        collapsed ? 'justify-center px-2' : 'justify-between px-4'
      )}>
        {!collapsed && (
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center flex-shrink-0">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-semibold text-text-primary truncate">CS Control Plane</span>
          </div>
        )}
        {collapsed && (
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
        )}
        {onToggle && !collapsed && (
          <button
            onClick={onToggle}
            className="p-1.5 rounded-md text-text-ghost hover:text-text-muted hover:bg-bg-active transition-colors"
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        )}
        {onToggle && collapsed && (
          <button
            onClick={onToggle}
            className="absolute -right-3 top-4 w-6 h-6 rounded-full bg-bg-elevated border border-border flex items-center justify-center text-text-ghost hover:text-text-muted transition-colors"
            aria-label="Expand sidebar"
          >
            <PanelLeft className="w-3 h-3" />
          </button>
        )}
        {onClose && (
          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-text-ghost hover:text-text-muted hover:bg-bg-active transition-colors"
            aria-label="Close navigation"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Main nav */}
      <nav className={cn('flex-1 py-3 overflow-y-auto', collapsed ? 'px-2' : 'px-3')}>
        <div className="space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavItem
              key={item.path}
              item={item}
              isActive={activeRoute === item.path}
              collapsed={collapsed}
            />
          ))}
        </div>
      </nav>

      {/* Bottom section */}
      <div className={cn('border-t border-border py-3', collapsed ? 'px-2' : 'px-3')}>
        {/* Settings */}
        {BOTTOM_ITEMS.map((item) => (
          <NavItem
            key={item.path}
            item={item}
            isActive={activeRoute === item.path}
            collapsed={collapsed}
          />
        ))}

        {/* Activity pulse + connection status */}
        {!collapsed && (
          <div className="mt-3 pt-3 border-t border-border">
            <div className="flex items-center gap-2 px-3 mb-2">
              <span
                className={cn(
                  'w-1.5 h-1.5 rounded-full flex-shrink-0',
                  connected ? 'bg-status-success' : 'bg-status-danger'
                )}
              />
              <span className="font-mono text-xxs text-text-ghost uppercase tracking-wider">
                {connected ? 'Live' : 'Offline'}
              </span>
            </div>
            {latestEvents.length > 0 && (
              <div className="space-y-1">
                {latestEvents.map((evt) => (
                  <div key={evt.id} className="px-3 py-1">
                    <p className="text-xxs text-text-ghost truncate">{evt.message}</p>
                    <p className="font-mono text-xxs text-text-ghost/60">{formatRelativeTime(evt.timestamp)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {collapsed && (
          <div className="mt-3 pt-3 border-t border-border flex justify-center">
            <span
              className={cn(
                'w-2 h-2 rounded-full',
                connected ? 'bg-status-success' : 'bg-status-danger'
              )}
              title={connected ? 'Connected' : 'Disconnected'}
            />
          </div>
        )}
      </div>
    </>
  )
}
