import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import useCustomerStore from '../stores/customerStore'
import CustomerHero from '../components/customers/CustomerHero'
import HealthStory from '../components/customers/HealthStory'
import IntelPanels from '../components/customers/IntelPanels'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'

export default function CustomerDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const {
    selectedCustomer, detailLoading, healthHistory,
    customerTickets, customerInsights, similarIssues,
    fetchAllDetail, clearDetail,
  } = useCustomerStore()

  useEffect(() => {
    if (id) fetchAllDetail(id)
    return () => clearDetail()
  }, [id, fetchAllDetail, clearDetail])

  if (detailLoading) {
    return (
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-5 space-y-4">
        <LoadingSkeleton variant="rect" width="100%" height={120} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <LoadingSkeleton variant="rect" height={240} />
          <LoadingSkeleton variant="rect" height={240} />
        </div>
      </div>
    )
  }

  if (!selectedCustomer) {
    return (
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-5">
        <p className="text-sm text-text-ghost py-20 text-center">Customer not found</p>
      </div>
    )
  }

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-5 space-y-4">
      {/* Back nav */}
      <button
        onClick={() => navigate('/customers')}
        className="flex items-center gap-1.5 text-xs text-text-ghost hover:text-text-muted transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Customers
      </button>

      {/* Hero */}
      <CustomerHero customer={selectedCustomer} />

      {/* Health trend + factors — 2 col */}
      <HealthStory
        healthHistory={healthHistory}
        customer={selectedCustomer}
      />

      {/* Tickets + Calls + Similar Issues */}
      <IntelPanels
        tickets={customerTickets}
        insights={customerInsights}
        similarIssues={similarIssues}
      />
    </div>
  )
}
