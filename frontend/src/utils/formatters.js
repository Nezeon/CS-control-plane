export function formatNumber(n) {
  if (n == null) return '—'
  if (Math.abs(n) >= 1000) {
    return new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(n)
  }
  return new Intl.NumberFormat('en').format(n)
}

export function formatTime(dateString) {
  if (!dateString) return '—'
  const d = new Date(dateString)
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
}

export function formatDate(dateString) {
  if (!dateString) return '—'
  const d = new Date(dateString)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function formatRelativeTime(dateString) {
  if (!dateString) return '—'
  const now = Date.now()
  const then = new Date(dateString).getTime()
  const diff = Math.max(0, now - then)
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export function formatPercentChange(value) {
  if (value == null) return ''
  const sign = value > 0 ? '+' : ''
  return `${sign}${value}`
}

export function getInitials(name) {
  if (!name) return '?'
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
}

/* ─── Color maps — Void Precision palette ─── */

const statusColorMap = {
  active: 'accent',
  processing: 'data',
  idle: 'text-ghost',
  healthy: 'status-success',
  watch: 'status-warning',
  high_risk: 'status-danger',
  critical: 'status-danger',
  error: 'status-danger',
}

export function getStatusColor(status) {
  return statusColorMap[status] || 'text-ghost'
}

const statusHexMap = {
  active: '#6366F1',
  processing: '#06B6D4',
  idle: '#52525B',
  healthy: '#22C55E',
  watch: '#EAB308',
  high_risk: '#EF4444',
  critical: '#EF4444',
  error: '#EF4444',
}

export function getStatusHex(status) {
  return statusHexMap[status] || '#52525B'
}

const severityColorMap = {
  P1: '#EF4444',
  P2: '#EAB308',
  P3: '#06B6D4',
  P4: '#71717A',
  critical: '#EF4444',
  high: '#EAB308',
  medium: '#06B6D4',
  low: '#71717A',
}

export function getSeverityColor(severity) {
  return severityColorMap[severity] || '#71717A'
}

const laneColorMap = {
  control: '#6366F1',
  value: '#22C55E',
  support: '#EAB308',
  delivery: '#06B6D4',
}

export function getLaneColor(lane) {
  return laneColorMap[lane] || '#71717A'
}

export function getRiskColor(riskLevel) {
  switch (riskLevel) {
    case 'high_risk': return '#EF4444'
    case 'critical': return '#EF4444'
    case 'watch': return '#EAB308'
    case 'healthy': return '#22C55E'
    default: return '#71717A'
  }
}

const eventTypeColorMap = {
  jira_ticket_created: '#6366F1',
  fathom_call_processed: '#06B6D4',
  zoom_call_completed: '#06B6D4',
  daily_health_check: '#22C55E',
  health_check: '#22C55E',
  new_alert: '#EAB308',
  alert_fired: '#EF4444',
}

export function getEventTypeColor(eventType) {
  return eventTypeColorMap[eventType] || '#6366F1'
}
