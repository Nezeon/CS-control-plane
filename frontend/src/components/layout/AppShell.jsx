import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import AlertsDrawer from './AlertsDrawer'

const PAGE_TITLES = {
  '/': 'Command Center',
  '/agents': 'Agents',
  '/customers': 'Customers',
}

function getPageTitle(pathname) {
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname]
  if (pathname.startsWith('/customers/')) return 'Customer Detail'
  return 'Command Center'
}

export default function AppShell({ children }) {
  const [collapsed, setCollapsed] = useState(false)
  const [theme, setTheme] = useState('dark')
  const [alertsOpen, setAlertsOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  const title = getPageTitle(location.pathname)

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-default)' }}>
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(prev => !prev)}
        theme={theme}
        onThemeToggle={toggleTheme}
      />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopBar
          title={title}
          onBellClick={() => setAlertsOpen(true)}
        />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
      <AlertsDrawer open={alertsOpen} onClose={() => setAlertsOpen(false)} />
    </div>
  )
}
