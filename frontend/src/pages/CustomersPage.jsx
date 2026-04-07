import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Users, UserPlus, ChevronDown } from 'lucide-react'
import CustomerTable from '../components/customers/CustomerTable'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { customerApi } from '../services/customerApi'

const PAGE_SIZE = 100

const HEALTH_FILTERS = [
  { label: 'All', value: null },
  { label: 'Healthy (80+)', value: 'healthy' },
  { label: 'Watch (50-79)', value: 'watch' },
  { label: 'At Risk (<50)', value: 'at_risk' },
]

const TYPE_TABS = [
  { key: 'active', label: 'Active Customers', icon: Users },
  { key: 'prospect', label: 'Prospects', icon: UserPlus },
]

function mapCustomer(c) {
  return {
    id: c.id,
    name: c.name,
    health_score: c.health_score,
    csm_owner: c.cs_owner?.full_name || '—',
    open_tickets: c.open_ticket_count ?? 0,
    last_meeting: c.last_call_date || null,
    arr: 0,
    segment: c.tier || 'Enterprise',
    risk_level: c.risk_level,
    renewal_date: c.renewal_date,
    deal_stage: c.deal_stage,
    deal_amount: c.deal_amount,
    deal_name: c.deal_name,
    industry: c.industry,
    primary_contact_name: c.primary_contact_name,
  }
}

export default function CustomersPage() {
  const navigate = useNavigate()
  const [customerType, setCustomerType] = useState('active')
  const [search, setSearch] = useState('')
  const [healthFilter, setHealthFilter] = useState(0)
  const [customers, setCustomers] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState(null)

  const fetchCustomers = useCallback((type, offset = 0, append = false) => {
    if (!append) setLoading(true)
    else setLoadingMore(true)
    setError(null)
    const params = { limit: PAGE_SIZE, offset, sort_by: type === 'prospect' ? 'name' : 'score', sort_order: 'asc', customer_type: type }
    customerApi.list(params)
      .then(({ data }) => {
        const list = (data?.customers || data || []).map(mapCustomer)
        setTotal(data?.total ?? list.length)
        if (append) {
          setCustomers(prev => [...prev, ...list])
        } else {
          setCustomers(list)
        }
      })
      .catch((err) => {
        console.error('Failed to fetch customers:', err.message)
        setError('Could not connect to backend. Make sure the API server is running on port 8000.')
        if (!append) setCustomers([])
      })
      .finally(() => { setLoading(false); setLoadingMore(false) })
  }, [])

  useEffect(() => {
    fetchCustomers(customerType)
  }, [customerType, fetchCustomers])

  const handleLoadMore = () => {
    fetchCustomers(customerType, customers.length, true)
  }

  const hasMore = customers.length < total

  const isProspect = customerType === 'prospect'

  const hf = HEALTH_FILTERS[healthFilter]
  const filtered = customers.filter(c => {
    const matchesSearch = !search || c.name.toLowerCase().includes(search.toLowerCase())
    if (isProspect) return matchesSearch
    if (!hf.value) return matchesSearch
    if (hf.value === 'healthy') return matchesSearch && (c.health_score ?? 0) >= 80
    if (hf.value === 'watch') return matchesSearch && (c.health_score ?? 0) >= 50 && (c.health_score ?? 0) < 80
    if (hf.value === 'at_risk') return matchesSearch && (c.health_score ?? 0) < 50
    return matchesSearch
  })

  const handleRowClick = (customer) => {
    navigate(`/customers/${customer.id}`)
  }

  const handleTypeChange = (type) => {
    setCustomerType(type)
    setSearch('')
    setHealthFilter(0)
  }

  return (
    <div className="space-y-6">
      {/* Type Toggle */}
      <div className="flex items-center gap-1 p-1 rounded-lg w-fit" style={{ background: 'var(--bg-hover)' }}>
        {TYPE_TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => handleTypeChange(key)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md cursor-pointer transition-all duration-150"
            style={{
              background: customerType === key ? 'var(--card-bg)' : 'transparent',
              color: customerType === key ? 'var(--primary)' : 'var(--text-muted)',
              boxShadow: customerType === key ? '0 1px 3px rgba(0,0,0,0.2)' : 'none',
            }}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-md"
          style={{ background: 'var(--bg-hover)', border: '1px solid var(--border)' }}
        >
          <Search size={14} style={{ color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder={isProspect ? 'Search prospects...' : 'Search customers...'}
            aria-label="Search by name"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="bg-transparent text-sm outline-none w-48"
            style={{ color: 'var(--text-primary)' }}
          />
        </div>

        {/* Health filters only for active customers */}
        {!isProspect && (
          <div className="flex items-center gap-2">
            {HEALTH_FILTERS.map((f, i) => (
              <button
                key={f.label}
                onClick={() => setHealthFilter(i)}
                className="px-3 py-1.5 text-xs font-medium rounded-full cursor-pointer transition-colors duration-150"
                style={{
                  background: healthFilter === i ? 'var(--primary)' : 'var(--bg-hover)',
                  color: healthFilter === i ? 'var(--primary-contrast)' : 'var(--text-secondary)',
                }}
              >
                {f.label}
              </button>
            ))}
          </div>
        )}

        <span className="text-xs ml-auto" style={{ color: 'var(--text-muted)' }}>
          {filtered.length} {isProspect ? 'prospect' : 'customer'}{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg p-4 text-sm" style={{ background: 'color-mix(in srgb, var(--status-danger) 10%, transparent)', color: 'var(--status-danger)', border: '1px solid var(--status-danger)' }}>
          {error}
        </div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map(i => <LoadingSkeleton key={i} />)}
        </div>
      ) : (
        <>
          <CustomerTable customers={filtered} onRowClick={handleRowClick} variant={customerType} />
          {hasMore && (
            <div className="flex justify-center pt-2">
              <button
                onClick={handleLoadMore}
                disabled={loadingMore}
                className="flex items-center gap-2 px-6 py-2 text-sm font-medium rounded-full cursor-pointer transition-colors duration-150"
                style={{
                  background: 'var(--bg-hover)',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border)',
                  opacity: loadingMore ? 0.6 : 1,
                }}
              >
                {loadingMore ? 'Loading...' : (<><ChevronDown size={14} /> Load more ({total - customers.length} remaining)</>)}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
