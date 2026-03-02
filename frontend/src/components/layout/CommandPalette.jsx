import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Fuse from 'fuse.js'
import {
  Search, LayoutDashboard, Users, Brain, Lightbulb, Ticket, BarChart3,
  Settings, Activity, Mic, FileText,
} from 'lucide-react'
import useCustomerStore from '../../stores/customerStore'

const PAGES = [
  { id: 'page-dashboard', label: 'Dashboard', description: 'Overview & metrics', icon: LayoutDashboard, action: '/', category: 'Pages' },
  { id: 'page-customers', label: 'Customers', description: 'Customer portfolio', icon: Users, action: '/customers', category: 'Pages' },
  { id: 'page-agents', label: 'Agents', description: 'AI agent monitoring', icon: Brain, action: '/agents', category: 'Pages' },
  { id: 'page-insights', label: 'Insights', description: 'Call intelligence', icon: Lightbulb, action: '/insights', category: 'Pages' },
  { id: 'page-tickets', label: 'Tickets', description: 'Support tickets', icon: Ticket, action: '/tickets', category: 'Pages' },
  { id: 'page-reports', label: 'Analytics', description: 'Charts & reports', icon: BarChart3, action: '/reports', category: 'Pages' },
  { id: 'page-settings', label: 'Settings', description: 'Preferences', icon: Settings, action: '/settings', category: 'Pages' },
]

const AGENTS = [
  'CS Orchestrator', 'Customer Memory Agent', 'Call Intelligence Agent',
  'Health Monitor', 'Ticket Triage Agent', 'Troubleshooter',
  'Escalation Manager', 'QBR Generator', 'SOW Analyzer', 'Deployment Intel',
].map((name, i) => ({
  id: `agent-${i}`,
  label: name,
  description: 'AI Agent',
  icon: Brain,
  action: '/agents',
  category: 'Agents',
}))

const ACTIONS = [
  { id: 'action-health', label: 'Run Health Check', description: 'Trigger health scoring', icon: Activity, action: 'health-check', category: 'Actions' },
  { id: 'action-fathom', label: 'Sync Fathom Recordings', description: 'Pull latest recordings', icon: Mic, action: 'sync-fathom', category: 'Actions' },
  { id: 'action-report', label: 'Generate Report', description: 'Create analytics report', icon: FileText, action: 'generate-report', category: 'Actions' },
]

export default function CommandPalette({ isOpen, onClose }) {
  const navigate = useNavigate()
  const inputRef = useRef(null)
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const customers = useCustomerStore((s) => s.customers)

  const allItems = useMemo(() => {
    const customerItems = (customers || []).slice(0, 20).map((c) => ({
      id: `customer-${c.id}`,
      label: c.name || c.company_name,
      description: c.tier || 'Customer',
      icon: Users,
      action: `/customers/${c.id}`,
      category: 'Customers',
    }))
    return [...PAGES, ...customerItems, ...AGENTS, ...ACTIONS]
  }, [customers])

  const fuse = useMemo(() => new Fuse(allItems, {
    keys: ['label', 'description'],
    threshold: 0.4,
  }), [allItems])

  const results = useMemo(() => {
    if (!query.trim()) return allItems.slice(0, 15)
    return fuse.search(query).slice(0, 15).map((r) => r.item)
  }, [query, fuse, allItems])

  useEffect(() => {
    if (isOpen) {
      setQuery('')
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen])

  useEffect(() => { setSelectedIndex(0) }, [query])

  const handleSelect = useCallback((item) => {
    onClose()
    if (item.category === 'Actions') return
    navigate(item.action)
  }, [navigate, onClose])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((p) => Math.min(p + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((p) => Math.max(p - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (results[selectedIndex]) handleSelect(results[selectedIndex])
    } else if (e.key === 'Escape') {
      onClose()
    }
  }, [results, selectedIndex, handleSelect, onClose])

  const grouped = useMemo(() => {
    const groups = {}
    for (const item of results) {
      if (!groups[item.category]) groups[item.category] = []
      groups[item.category].push(item)
    }
    return groups
  }, [results])

  let flatIndex = -1

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -8 }}
            transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
            className="fixed top-[20%] left-1/2 -translate-x-1/2 z-[101] w-full max-w-[560px] px-4"
          >
            <div
              data-testid="command-palette"
              className="bg-bg-elevated border border-border-strong rounded-xl overflow-hidden shadow-2xl"
            >
              {/* Search input */}
              <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
                <Search className="w-4 h-4 text-text-ghost flex-shrink-0" />
                <input
                  ref={inputRef}
                  data-testid="command-palette-input"
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Search commands, customers, agents..."
                  className="flex-1 bg-transparent outline-none text-sm text-text-primary placeholder:text-text-ghost"
                />
              </div>

              {/* Results */}
              <div data-testid="command-palette-results" className="max-h-[360px] overflow-y-auto py-1">
                {Object.entries(grouped).map(([category, items]) => (
                  <div key={category}>
                    <div className="px-4 pt-3 pb-1">
                      <span className="font-mono text-xxs font-medium uppercase tracking-wider text-text-ghost">
                        {category}
                      </span>
                    </div>
                    {items.map((item) => {
                      flatIndex++
                      const isSelected = flatIndex === selectedIndex
                      const Icon = item.icon
                      const idx = flatIndex
                      return (
                        <button
                          key={item.id}
                          onClick={() => handleSelect(item)}
                          onMouseEnter={() => setSelectedIndex(idx)}
                          className={`flex items-center gap-3 w-full px-4 py-2 text-left transition-colors ${
                            isSelected ? 'bg-bg-active' : 'hover:bg-bg-active/50'
                          }`}
                        >
                          <Icon className={`w-4 h-4 flex-shrink-0 ${isSelected ? 'text-accent' : 'text-text-ghost'}`} />
                          <div className="flex-1 min-w-0">
                            <span className={`text-sm ${isSelected ? 'text-text-primary' : 'text-text-secondary'}`}>
                              {item.label}
                            </span>
                            {item.description && (
                              <span className="ml-2 text-xs text-text-ghost">{item.description}</span>
                            )}
                          </div>
                        </button>
                      )
                    })}
                  </div>
                ))}
                {results.length === 0 && (
                  <div className="px-4 py-8 text-center text-sm text-text-ghost">
                    No results for &ldquo;{query}&rdquo;
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
