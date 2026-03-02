import { useState, useEffect, useCallback } from 'react'
import { useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import CommandPalette from './CommandPalette'
import ToastContainer from './ToastContainer'
import { cn } from '../../utils/cn'

const SIDEBAR_KEY = 'sidebar-collapsed'

export default function AppLayout({ children }) {
  const location = useLocation()
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try {
      return localStorage.getItem(SIDEBAR_KEY) === 'true'
    } catch {
      return false
    }
  })

  const openPalette = useCallback(() => setCommandPaletteOpen(true), [])
  const closePalette = useCallback(() => setCommandPaletteOpen(false), [])

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => {
      const next = !prev
      try { localStorage.setItem(SIDEBAR_KEY, String(next)) } catch {}
      return next
    })
  }, [])

  // Cmd+K / Ctrl+K global shortcut
  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandPaletteOpen((prev) => !prev)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const reducedMotion = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  const pageVariants = {
    initial: { opacity: 0, y: reducedMotion ? 0 : 4 },
    animate: { opacity: 1, y: 0, transition: { duration: reducedMotion ? 0.01 : 0.25, ease: [0.16, 1, 0.3, 1] } },
    exit: { opacity: 0, transition: { duration: reducedMotion ? 0.01 : 0.15 } },
  }

  return (
    <>
      {/* Skip to content */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:rounded-lg focus:bg-bg-elevated focus:text-accent focus:font-mono focus:text-xs"
      >
        Skip to content
      </a>

      <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />

      <div className={cn(
        'min-h-screen transition-[margin-left] duration-200 ease-out-expo',
        sidebarCollapsed ? 'ml-16' : 'ml-60',
        'max-md:ml-0'
      )}>
        <TopBar onOpenCommandPalette={openPalette} />

        <main id="main-content" data-testid="main-content" className="relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      <CommandPalette isOpen={commandPaletteOpen} onClose={closePalette} />
      <ToastContainer />
    </>
  )
}
