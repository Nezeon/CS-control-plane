import { useEffect } from 'react'
import { motion } from 'framer-motion'
import useDashboardStore from '../stores/dashboardStore'
import FloatingOrbsGrid from '../components/dashboard/FloatingOrbsGrid'
import NeuralSphereWrapper from '../components/dashboard/NeuralSphereWrapper'
import LivePulse from '../components/dashboard/LivePulse'
import HealthTerrainWrapper from '../components/dashboard/HealthTerrainWrapper'

const fadeUp = {
  initial: { opacity: 0, y: 6 },
  animate: { opacity: 1, y: 0 },
}

export default function DashboardPage() {
  const fetchAll = useDashboardStore((s) => s.fetchAll)

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const now = new Date()
  const dateStr = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
  const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-5 space-y-5">
      {/* Header */}
      <motion.div {...fadeUp} transition={{ duration: 0.3 }} className="flex items-baseline justify-between">
        <h1 className="text-xl font-semibold text-text-primary">Dashboard</h1>
        <p className="text-xs text-text-ghost font-mono tabular-nums">{dateStr} · {timeStr}</p>
      </motion.div>

      {/* KPI Row */}
      <motion.div {...fadeUp} transition={{ duration: 0.3, delay: 0.05 }}>
        <FloatingOrbsGrid />
      </motion.div>

      {/* Agent Status + Activity Feed — 2 col */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <motion.div {...fadeUp} transition={{ duration: 0.3, delay: 0.1 }} className="lg:col-span-3">
          <NeuralSphereWrapper />
        </motion.div>
        <motion.div {...fadeUp} transition={{ duration: 0.3, delay: 0.15 }} className="lg:col-span-2">
          <LivePulse />
        </motion.div>
      </div>

      {/* Customer Health Overview */}
      <motion.div {...fadeUp} transition={{ duration: 0.3, delay: 0.2 }}>
        <HealthTerrainWrapper />
      </motion.div>
    </div>
  )
}
