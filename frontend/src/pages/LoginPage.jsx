import { useState, useEffect, Suspense, lazy, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Loader2, Shield, Cpu, Activity, Users } from 'lucide-react'
import useAuthStore from '../stores/authStore'
import { seedDashboardStats, seedAgents } from '../data/dashboard'

const NeuralSphere3D = lazy(() => import('../three/NeuralSphere'))

// Map seed agents to the format NeuralSphere expects
const sphereAgents = seedAgents.map((a) => ({
  name: a.id,
  display_name: a.name,
  lane: a.lane,
  status: a.status,
  tasks_today: a.tasks_today,
}))

export default function LoginPage() {
  const navigate = useNavigate()
  const { login, isAuthenticated, isLoading, error } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  useEffect(() => {
    if (isAuthenticated) navigate('/', { replace: true })
  }, [isAuthenticated, navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email || !password) return
    try {
      await login(email, password)
      navigate('/', { replace: true })
    } catch { /* Error set in store */ }
  }

  const stats = seedDashboardStats
  const activeCount = seedAgents.filter((a) => a.status === 'active').length

  return (
    <div data-testid="login-page" className="relative flex min-h-screen bg-bg overflow-hidden">
      {/* Subtle gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-accent/[0.03] via-transparent to-data/[0.02]" />

      {/* Left panel — 3D sphere + branding */}
      <div className="hidden lg:flex flex-1 relative items-center justify-center overflow-hidden">
        {/* 3D Neural Sphere */}
        <div className="absolute inset-0 flex items-center justify-center opacity-60">
          <Suspense fallback={null}>
            <div className="w-full h-full max-w-[600px] max-h-[600px]">
              <NeuralSphere3D agents={sphereAgents} />
            </div>
          </Suspense>
        </div>

        {/* Content overlay */}
        <div className="relative z-10 text-center px-12 mt-32">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="w-14 h-14 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto mb-5">
              <Shield className="w-7 h-7 text-accent" />
            </div>
            <h2 className="text-2xl font-semibold text-text-primary mb-2">CS Control Plane</h2>
            <p className="text-sm text-text-muted max-w-md mx-auto leading-relaxed">
              AI-powered customer success orchestration platform
            </p>
          </motion.div>

          {/* Live KPI cards */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="flex items-center justify-center gap-3 mt-8"
          >
            <KpiPill icon={Activity} value={`${Math.round(stats.avg_health)}%`} label="Avg Health" />
            <KpiPill icon={Users} value={stats.total_customers} label="Customers" />
            <KpiPill icon={Cpu} value={`${activeCount}/${stats.total_agents}`} label="Agents Active" />
          </motion.div>
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex-1 lg:max-w-md flex items-center justify-center px-6 py-12 relative z-10">
        <motion.div
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.15 }}
          className="w-full max-w-sm"
        >
          {/* Mobile-only header */}
          <div className="lg:hidden text-center mb-8">
            <div className="w-11 h-11 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto mb-3">
              <Shield className="w-5 h-5 text-accent" />
            </div>
            <h1 className="text-lg font-semibold text-text-primary">CS Control Plane</h1>
          </div>

          {/* Desktop form header */}
          <div className="hidden lg:block mb-6">
            <h1 className="text-xl font-semibold text-text-primary">Sign in</h1>
            <p className="text-sm text-text-muted mt-1">Enter your credentials to continue</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="login-email" className="block text-xs font-medium text-text-muted mb-1.5">
                Email
              </label>
              <input
                id="login-email"
                data-testid="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@hivepro.com"
                className="w-full px-3.5 py-2.5 rounded-lg bg-bg-subtle border border-border text-sm text-text-primary placeholder:text-text-ghost focus:border-accent focus:outline-none transition-colors"
                autoComplete="email"
              />
            </div>

            <div>
              <label htmlFor="login-password" className="block text-xs font-medium text-text-muted mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  id="login-password"
                  data-testid="login-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full px-3.5 py-2.5 pr-10 rounded-lg bg-bg-subtle border border-border text-sm text-text-primary placeholder:text-text-ghost focus:border-accent focus:outline-none transition-colors"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-ghost hover:text-text-muted transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <p data-testid="login-error" className="text-xs text-status-danger text-center py-1">{error}</p>
            )}

            <button
              data-testid="login-submit"
              type="submit"
              disabled={isLoading || !email || !password}
              className="w-full py-2.5 mt-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent-hover transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in...
                </span>
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          <p className="text-xxs text-text-ghost text-center mt-6">
            Demo mode — any email and password will work
          </p>
        </motion.div>
      </div>
    </div>
  )
}

function KpiPill({ icon: Icon, value, label }) {
  return (
    <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-lg bg-bg-subtle/80 border border-border backdrop-blur-sm">
      <Icon className="w-3.5 h-3.5 text-text-ghost" />
      <div>
        <p className="text-sm font-semibold text-text-primary font-mono tabular-nums">{value}</p>
        <p className="text-xxs text-text-ghost">{label}</p>
      </div>
    </div>
  )
}
