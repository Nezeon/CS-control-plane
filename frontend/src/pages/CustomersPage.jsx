import { useEffect, useCallback, useRef, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Search, LayoutGrid, List, ShieldAlert, ShieldCheck, Eye } from 'lucide-react'
import useCustomerStore from '../stores/customerStore'
import PremiumGrid from '../components/customers/PremiumGrid'
import DataTable from '../components/customers/DataTable'
import QuickIntelPanel from '../components/customers/QuickIntelPanel'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'

export default function CustomersPage() {
  const navigate = useNavigate()
  const {
    customers, total, isLoading, viewMode,
    search, risk_level, tier, sort_by,
    setSearch, setRiskLevel, setTier, setSortBy, setViewMode,
    setHoveredCustomer, hoveredCustomer, fetchCustomers,
  } = useCustomerStore()

  const debounceRef = useRef(null)

  useEffect(() => { fetchCustomers() }, [fetchCustomers])

  const handleSearch = useCallback((val) => {
    setSearch(val)
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => fetchCustomers(), 300)
  }, [setSearch, fetchCustomers])

  const handleFilterChange = useCallback((setter) => (val) => {
    setter(val)
    setTimeout(() => fetchCustomers(), 0)
  }, [fetchCustomers])

  // Risk distribution counts
  const riskCounts = useMemo(() => {
    if (!customers?.length) return { healthy: 0, watch: 0, high_risk: 0 }
    return {
      healthy: customers.filter((c) => c.risk_level === 'healthy').length,
      watch: customers.filter((c) => c.risk_level === 'watch').length,
      high_risk: customers.filter((c) => c.risk_level === 'high_risk').length,
    }
  }, [customers])

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-5 space-y-4">
      {/* Header */}
      <div className="flex items-baseline justify-between">
        <h1 className="text-xl font-semibold text-text-primary">Customers</h1>
        <span className="text-xs text-text-ghost font-mono tabular-nums">{total || customers?.length || 0} total</span>
      </div>

      {/* Risk pills */}
      <div className="flex items-center gap-2">
        {[
          { key: null, label: 'All', count: total || customers?.length || 0, cls: '' },
          { key: 'healthy', label: 'Healthy', count: riskCounts.healthy, cls: 'text-status-success' },
          { key: 'watch', label: 'Watch', count: riskCounts.watch, cls: 'text-status-warning' },
          { key: 'high_risk', label: 'At Risk', count: riskCounts.high_risk, cls: 'text-status-danger' },
        ].map((pill) => (
          <button
            key={pill.label}
            onClick={() => handleFilterChange(setRiskLevel)(pill.key || '')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              (risk_level || '') === (pill.key || '')
                ? 'bg-accent/15 text-accent border border-accent/20'
                : 'bg-bg-active/50 text-text-muted border border-border-subtle hover:border-border'
            }`}
          >
            <span className={pill.cls}>{pill.count}</span> {pill.label}
          </button>
        ))}
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-ghost" />
          <input
            type="text"
            placeholder="Search customers..."
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-bg-subtle border border-border text-sm text-text-primary placeholder:text-text-ghost focus:border-accent focus:outline-none transition-colors"
          />
        </div>

        <select
          value={tier}
          onChange={(e) => handleFilterChange(setTier)(e.target.value)}
          className="px-3 py-2 rounded-lg bg-bg-subtle border border-border text-sm text-text-secondary focus:border-accent focus:outline-none"
        >
          <option value="">All Tiers</option>
          <option value="enterprise">Enterprise</option>
          <option value="mid_market">Mid-Market</option>
          <option value="smb">SMB</option>
        </select>

        <select
          value={sort_by}
          onChange={(e) => handleFilterChange(setSortBy)(e.target.value)}
          className="px-3 py-2 rounded-lg bg-bg-subtle border border-border text-sm text-text-secondary focus:border-accent focus:outline-none"
        >
          <option value="health_score">Sort: Health</option>
          <option value="company_name">Sort: Name</option>
          <option value="risk_level">Sort: Risk</option>
          <option value="contract_end">Sort: Renewal</option>
        </select>

        {/* View toggle */}
        <div className="flex items-center gap-1 ml-auto">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-md transition-colors ${viewMode === 'grid' ? 'bg-accent/15 text-accent' : 'text-text-ghost hover:text-text-muted'}`}
            aria-label="Grid view"
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`p-2 rounded-md transition-colors ${viewMode === 'table' ? 'bg-accent/15 text-accent' : 'text-text-ghost hover:text-text-muted'}`}
            aria-label="Table view"
          >
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {[1, 2, 3, 4, 5, 6].map((i) => <LoadingSkeleton key={i} variant="card" height={140} />)}
        </div>
      ) : viewMode === 'grid' ? (
        <PremiumGrid
          customers={customers}
          onCustomerClick={(c) => navigate(`/customers/${c.id}`)}
          onHover={setHoveredCustomer}
        />
      ) : (
        <DataTable
          customers={customers}
          onCustomerClick={(c) => navigate(`/customers/${c.id}`)}
          onHover={setHoveredCustomer}
        />
      )}

      <QuickIntelPanel customer={hoveredCustomer} />
    </div>
  )
}
