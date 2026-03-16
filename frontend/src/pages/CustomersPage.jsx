import { useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import useCustomerStore from '../stores/customerStore'
import PillFilter from '../components/shared/PillFilter'
import HealthRing from '../components/shared/HealthRing'
import StatusPill from '../components/shared/StatusPill'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { formatDate } from '../utils/formatters'

const RISK_OPTIONS = [
  { value: '', label: 'All Risk' },
  { value: 'critical', label: 'Critical' },
  { value: 'high_risk', label: 'High Risk' },
  { value: 'watch', label: 'Watch' },
  { value: 'healthy', label: 'Healthy' },
]

const TIER_OPTIONS = [
  { value: '', label: 'All Tiers' },
  { value: 'enterprise', label: 'Enterprise' },
  { value: 'mid_market', label: 'Mid-Market' },
  { value: 'smb', label: 'SMB' },
]

export default function CustomersPage() {
  const navigate = useNavigate()
  const {
    customers, isLoading, search, risk_level, tier,
    setSearch, setRiskLevel, setTier, fetchCustomers,
  } = useCustomerStore()

  useEffect(() => {
    fetchCustomers()
  }, [fetchCustomers])

  const handleSearch = useCallback((e) => {
    setSearch(e.target.value)
  }, [setSearch])

  useEffect(() => {
    const timeout = setTimeout(() => fetchCustomers(), 300)
    return () => clearTimeout(timeout)
  }, [search, risk_level, tier, fetchCustomers])

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-display font-bold text-text-primary">Customers</h1>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-ghost" />
          <input
            type="text"
            value={search}
            onChange={handleSearch}
            placeholder="Search customers..."
            className="w-full pl-9 pr-3 py-2 text-sm bg-bg-subtle border border-border rounded-lg text-text-primary placeholder:text-text-ghost focus:outline-none focus:border-accent"
          />
        </div>
        <PillFilter options={RISK_OPTIONS} value={risk_level} onChange={setRiskLevel} />
        <PillFilter options={TIER_OPTIONS} value={tier} onChange={setTier} />
      </div>

      {/* Table */}
      {isLoading && customers.length === 0 ? (
        <LoadingSkeleton variant="card" count={3} />
      ) : customers.length === 0 ? (
        <p className="text-sm text-text-muted py-8 text-center">No customers found</p>
      ) : (
        <div className="glass-near rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-text-muted font-mono text-xxs uppercase tracking-wider border-b border-border-subtle">
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Industry</th>
                  <th className="px-4 py-3">Tier</th>
                  <th className="px-4 py-3">Health</th>
                  <th className="px-4 py-3">Risk</th>
                  <th className="px-4 py-3">Tickets</th>
                  <th className="px-4 py-3">Renewal</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((c) => (
                  <tr
                    key={c.id}
                    onClick={() => navigate(`/customers/${c.id}`)}
                    className="border-b border-border-subtle/50 hover:bg-bg-hover/50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 font-medium text-text-primary">{c.name}</td>
                    <td className="px-4 py-3 text-text-muted">{c.industry || '—'}</td>
                    <td className="px-4 py-3">
                      <span className="text-xxs font-mono uppercase px-2 py-0.5 rounded-full bg-bg-active text-text-secondary">
                        {c.tier || '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <HealthRing score={c.health_score ?? c.current_health} size={28} strokeWidth={3} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusPill status={c.risk_level || 'healthy'} />
                    </td>
                    <td className="px-4 py-3 font-mono text-text-muted">{c.open_tickets ?? '—'}</td>
                    <td className="px-4 py-3 text-text-muted text-xs">{formatDate(c.renewal_date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
