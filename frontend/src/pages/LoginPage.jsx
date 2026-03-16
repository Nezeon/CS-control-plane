import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { m } from 'framer-motion'
import { Zap, Eye, EyeOff, Loader2 } from 'lucide-react'
import useAuthStore from '../stores/authStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login, isAuthenticated, isLoading, error } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [demoLoading, setDemoLoading] = useState(false)

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

  const handleDemo = () => {
    setDemoLoading(true)
    // Demo mode: bypass API entirely, set demo token directly
    localStorage.setItem('access_token', 'demo-token')
    useAuthStore.setState({
      user: { id: 'demo-001', email: 'demo@hivepro.com', full_name: 'Demo User', role: 'cs_manager' },
      accessToken: 'demo-token',
      isAuthenticated: true,
      isLoading: false,
      error: null,
    })
    navigate('/', { replace: true })
  }

  const trustedCompanies = ['Acme Corp', 'Beta Financial', 'Gamma Telecom', 'Delta Health', 'Epsilon Insurance']

  return (
    <div data-testid="login-page" className="flex min-h-screen bg-void overflow-hidden">
      {/* Left panel — gradient branding (60%) */}
      <div className="hidden lg:flex lg:w-[60%] relative items-center justify-center overflow-hidden">
        {/* Animated gradient background */}
        <div
          className="absolute inset-0"
          style={{
            background: [
              'radial-gradient(ellipse 80% 60% at 30% 70%, rgba(124, 92, 252, 0.15) 0%, transparent 60%)',
              'radial-gradient(ellipse 60% 80% at 70% 30%, rgba(0, 229, 196, 0.10) 0%, transparent 60%)',
              'radial-gradient(ellipse 50% 50% at 50% 50%, rgba(59, 158, 255, 0.06) 0%, transparent 70%)',
            ].join(', '),
            animation: 'atmosphereShift 30s ease-in-out infinite alternate',
          }}
        />

        {/* Secondary moving gradient */}
        <div
          className="absolute inset-0 opacity-60"
          style={{
            background: [
              'radial-gradient(ellipse 50% 40% at 60% 80%, rgba(124, 92, 252, 0.08) 0%, transparent 50%)',
              'radial-gradient(ellipse 40% 50% at 20% 20%, rgba(0, 229, 196, 0.06) 0%, transparent 50%)',
            ].join(', '),
            animation: 'atmosphereShift 24s ease-in-out infinite alternate-reverse',
          }}
        />

        {/* Content */}
        <div className="relative z-10 text-center px-12">
          <m.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col items-center"
          >
            {/* Logo */}
            <div className="w-20 h-20 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center mb-8">
              <Zap className="w-10 h-10 text-accent" />
            </div>

            {/* Title */}
            <h1 className="font-display text-4xl font-bold text-text-primary mb-3">
              HivePro CS
            </h1>

            {/* Tagline */}
            <p className="text-lg text-text-secondary max-w-md leading-relaxed">
              AI-Powered Customer Success
            </p>

            {/* Decorative line */}
            <div className="w-16 h-px bg-gradient-to-r from-transparent via-accent/40 to-transparent mt-8 mb-8" />

            <p className="text-sm text-text-muted max-w-sm leading-relaxed">
              Orchestrate 13 AI agents across 4 tiers to automate customer success workflows in real-time.
            </p>
          </m.div>

          {/* Trusted by */}
          <m.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="absolute bottom-12 left-0 right-0 px-12"
          >
            <p className="text-xxs font-mono uppercase tracking-widest text-text-ghost mb-4">
              Trusted by
            </p>
            <div className="flex items-center justify-center gap-6 flex-wrap">
              {trustedCompanies.map((name) => (
                <span
                  key={name}
                  className="text-xs text-text-ghost/80 font-medium"
                >
                  {name}
                </span>
              ))}
            </div>
          </m.div>
        </div>
      </div>

      {/* Right panel — login form (40%) */}
      <div className="flex-1 lg:w-[40%] flex items-center justify-center px-6 py-12 bg-bg-subtle/30">
        <m.div
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="w-full max-w-sm"
        >
          {/* Mobile-only header */}
          <div className="lg:hidden text-center mb-10">
            <div className="w-14 h-14 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto mb-4">
              <Zap className="w-7 h-7 text-accent" />
            </div>
            <h1 className="font-display text-2xl font-bold text-text-primary">HivePro CS</h1>
            <p className="text-sm text-text-secondary mt-1">AI-Powered Customer Success</p>
          </div>

          {/* Glass card form */}
          <div className="glass-near p-8">
            {/* Header */}
            <div className="mb-6">
              <h2 className="font-display text-xl font-semibold text-text-primary">
                Welcome back
              </h2>
              <p className="text-sm text-text-secondary mt-1">
                Sign in to your account
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email */}
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

              {/* Password */}
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

              {/* Error */}
              {error && (
                <p data-testid="login-error" className="text-xs text-status-danger text-center py-1">
                  {error}
                </p>
              )}

              {/* Sign in button */}
              <button
                data-testid="login-submit"
                type="submit"
                disabled={isLoading || !email || !password}
                className="btn-gradient w-full py-2.5 text-sm disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
              >
                {isLoading && !demoLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Signing in...
                  </span>
                ) : (
                  'Sign in'
                )}
              </button>
            </form>

            {/* Separator */}
            <div className="flex items-center gap-3 my-5">
              <div className="flex-1 h-px bg-border" />
              <span className="text-xxs text-text-ghost">or</span>
              <div className="flex-1 h-px bg-border" />
            </div>

            {/* Continue as Demo */}
            <button
              onClick={handleDemo}
              disabled={isLoading || demoLoading}
              className="w-full py-2.5 rounded-xl text-sm font-medium text-text-secondary border border-border hover:border-accent hover:text-text-primary transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {demoLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading demo...
                </span>
              ) : (
                'Continue as Demo'
              )}
            </button>
          </div>
        </m.div>
      </div>
    </div>
  )
}
