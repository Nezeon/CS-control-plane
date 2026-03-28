import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import CustomerTable from '../components/customers/CustomerTable'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { customerApi } from '../services/customerApi'

const HEALTH_FILTERS = [
  { label: 'All', value: null },
  { label: 'Healthy (80+)', value: 'healthy' },
  { label: 'Watch (50-79)', value: 'watch' },
  { label: 'At Risk (<50)', value: 'at_risk' },
]

export default function CustomersPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [healthFilter, setHealthFilter] = useState(0)
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    customerApi.list({ limit: 100, sort_by: 'score', sort_order: 'asc' })
      .then(({ data }) => {
        const list = data?.customers || data || []
        setCustomers(list.map(c => ({
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
        })))
      })
      .catch((err) => {
        console.error('Failed to fetch customers:', err.message)
        setError('Could not connect to backend. Make sure the API server is running on port 8000.')
        setCustomers([])
      })
      .finally(() => setLoading(false))
  }, [])

  const hf = HEALTH_FILTERS[healthFilter]
  const filtered = customers.filter(c => {
    const matchesSearch = !search || c.name.toLowerCase().includes(search.toLowerCase())
    if (!hf.value) return matchesSearch
    if (hf.value === 'healthy') return matchesSearch && (c.health_score ?? 0) >= 80
    if (hf.value === 'watch') return matchesSearch && (c.health_score ?? 0) >= 50 && (c.health_score ?? 0) < 80
    if (hf.value === 'at_risk') return matchesSearch && (c.health_score ?? 0) < 50
    return matchesSearch
  })

  const handleRowClick = (customer) => {
    navigate(`/customers/${customer.id}`)
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map(i => <LoadingSkeleton key={i} />)}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-md"
          style={{ background: 'var(--bg-hover)', border: '1px solid var(--border)' }}
        >
          <Search size={14} style={{ color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search customers..."
            aria-label="Search customers by name"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="bg-transparent text-sm outline-none w-48"
            style={{ color: 'var(--text-primary)' }}
          />
        </div>

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

        <span className="text-xs ml-auto" style={{ color: 'var(--text-muted)' }}>
          {filtered.length} customer{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg p-4 text-sm" style={{ background: 'color-mix(in srgb, var(--status-danger) 10%, transparent)', color: 'var(--status-danger)', border: '1px solid var(--status-danger)' }}>
          {error}
        </div>
      )}

      {/* Table */}
      <CustomerTable customers={filtered} onRowClick={handleRowClick} />
    </div>
  )
}
