import { useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import { Users, HeartPulse, CheckCircle, Phone, X } from 'lucide-react'
import useReportStore from '../stores/reportStore'
import HealthHeatmap from '../components/reports/HealthHeatmap'
import TicketVelocity from '../components/reports/TicketVelocity'
import SentimentRiver from '../components/reports/SentimentRiver'
import AgentThroughput from '../components/reports/AgentThroughput'
import ReportList from '../components/reports/ReportList'

function KpiCard({ icon: Icon, value, label, suffix = '', trend }) {
  const isPositive = trend > 0
  return (
    <div className="card p-3">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
          <Icon className="w-4 h-4 text-accent" />
        </div>
        {trend != null && trend !== 0 && (
          <span className={`text-[10px] font-mono font-semibold ${isPositive ? 'text-status-success' : 'text-status-danger'}`}>
            {isPositive ? '+' : ''}{typeof trend === 'number' ? trend.toFixed(1) : trend}%
          </span>
        )}
      </div>
      <div className="text-xl font-bold text-text-primary tabular-nums leading-none">
        {value}{suffix}
      </div>
      <div className="text-[10px] font-mono text-text-ghost uppercase mt-1">{label}</div>
    </div>
  )
}

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } },
}

const stagger = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
}

export default function ReportsPage() {
  const fetchAll = useReportStore((s) => s.fetchAll)
  const isLoading = useReportStore((s) => s.isLoading)
  const reportsLoading = useReportStore((s) => s.reportsLoading)
  const kpis = useReportStore((s) => s.kpis)
  const healthTrend = useReportStore((s) => s.healthTrend)
  const ticketVolume = useReportStore((s) => s.ticketVolume)
  const sentimentStream = useReportStore((s) => s.sentimentStream)
  const agentPerformance = useReportStore((s) => s.agentPerformance)
  const reports = useReportStore((s) => s.reports)
  const crossFilter = useReportStore((s) => s.crossFilter)
  const clearCrossFilter = useReportStore((s) => s.clearCrossFilter)

  useEffect(() => { fetchAll() }, [fetchAll])

  const kpiCards = useMemo(() => [
    { value: kpis?.total_customers ?? kpis?.customers ?? 0, label: 'Customers', trend: kpis?.customer_trend, icon: Users },
    { value: kpis?.avg_health ?? kpis?.average_health ?? 0, label: 'Avg Health', suffix: '%', trend: kpis?.health_trend, icon: HeartPulse },
    { value: kpis?.tickets_resolved ?? kpis?.resolved ?? 0, label: 'Resolved', trend: kpis?.resolved_trend, icon: CheckCircle },
    { value: kpis?.total_calls ?? kpis?.calls ?? 0, label: 'Calls', trend: kpis?.calls_trend, icon: Phone },
  ], [kpis])

  return (
    <motion.div data-testid="reports-page" className="h-full flex flex-col" variants={stagger} initial="hidden" animate="show">
      <motion.div variants={fadeUp} className="pb-4">
        <h1 className="text-xl font-semibold text-text-primary">Analytics</h1>
      </motion.div>

      <div className="flex-1 overflow-y-auto pb-8">
        {/* KPIs */}
        <motion.div variants={fadeUp} className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
          {kpiCards.map((kpi) => (
            <KpiCard key={kpi.label} icon={kpi.icon} value={kpi.value} label={kpi.label} suffix={kpi.suffix || ''} trend={kpi.trend} />
          ))}
        </motion.div>

        {/* Cross filter pill */}
        {crossFilter && (
          <motion.div className="flex justify-center mb-4" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
            <button
              onClick={clearCrossFilter}
              data-testid="cross-filter-pill"
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent/10 border border-accent/20 text-xs text-accent hover:bg-accent/15 transition-colors"
            >
              <span className="font-mono">Filtered:</span>
              <span className="font-semibold">{crossFilter.type} = {crossFilter.value}</span>
              <X className="w-3 h-3 ml-1" />
            </button>
          </motion.div>
        )}

        {/* Charts */}
        <motion.div variants={fadeUp} className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <HealthHeatmap data={healthTrend} isLoading={isLoading} />
          <TicketVelocity data={ticketVolume} isLoading={isLoading} />
          <SentimentRiver data={sentimentStream} isLoading={isLoading} />
          <AgentThroughput data={agentPerformance} isLoading={isLoading} />
        </motion.div>

        {/* Reports */}
        <motion.div variants={fadeUp}>
          <ReportList reports={reports} isLoading={reportsLoading} />
        </motion.div>
      </div>
    </motion.div>
  )
}
