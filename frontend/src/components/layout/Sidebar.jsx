import { NavLink, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  Bot,
  Users,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/agents', label: 'Agents', icon: Bot },
  { to: '/customers', label: 'Customers', icon: Users },
]

export default function Sidebar({ collapsed, onToggle, theme, onThemeToggle }) {
  const location = useLocation()

  return (
    <motion.aside
      animate={{ width: collapsed ? 64 : 220 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
      className="flex flex-col h-screen border-r"
      style={{
        background: 'var(--bg-sidebar)',
        borderColor: 'var(--border)',
      }}
    >
      {/* Logo area */}
      <div className="flex items-center h-[45px] px-4 border-b" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-2 overflow-hidden">
          <div
            className="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 text-xs font-bold"
            style={{ background: 'var(--primary)', color: 'var(--primary-contrast)' }}
          >
            H
          </div>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-sm font-medium whitespace-nowrap"
              style={{ color: 'var(--text-primary)' }}
            >
              HivePro
            </motion.span>
          )}
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex-1 py-3 px-2 flex flex-col gap-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
          const isActive = to === '/' ? location.pathname === '/' : location.pathname.startsWith(to)
          return (
            <NavLink
              key={to}
              to={to}
              className="flex items-center gap-3 rounded-md transition-colors duration-150 cursor-pointer"
              style={{
                padding: collapsed ? '8px 0' : '8px 12px',
                justifyContent: collapsed ? 'center' : 'flex-start',
                background: isActive ? 'var(--bg-hover)' : 'transparent',
                color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                borderLeft: isActive ? '3px solid var(--primary)' : '3px solid transparent',
              }}
            >
              <Icon size={18} />
              {!collapsed && (
                <span className="text-sm whitespace-nowrap">{label}</span>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Bottom section */}
      <div className="px-2 pb-3 flex flex-col gap-2">
        {/* Theme toggle */}
        <button
          onClick={onThemeToggle}
          className="flex items-center gap-3 rounded-md transition-colors duration-150 cursor-pointer"
          style={{
            padding: collapsed ? '8px 0' : '8px 12px',
            justifyContent: collapsed ? 'center' : 'flex-start',
            color: 'var(--text-secondary)',
          }}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          {!collapsed && (
            <span className="text-sm">{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
          )}
        </button>

        {/* Collapse toggle */}
        <button
          onClick={onToggle}
          className="flex items-center gap-3 rounded-md transition-colors duration-150 cursor-pointer"
          style={{
            padding: collapsed ? '8px 0' : '8px 12px',
            justifyContent: collapsed ? 'center' : 'flex-start',
            color: 'var(--text-secondary)',
            background: 'var(--bg-hover)',
          }}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          {!collapsed && <span className="text-sm">Collapse</span>}
        </button>
      </div>
    </motion.aside>
  )
}
