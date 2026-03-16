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

/* ─── Color maps — Obsidian Luxe palette ─── */

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
  active: '#7C5CFC',
  processing: '#3B9EFF',
  idle: '#5C5C72',
  healthy: '#00E5A0',
  watch: '#FFB547',
  high_risk: '#FF5C5C',
  critical: '#FF5C5C',
  error: '#FF5C5C',
}

export function getStatusHex(status) {
  return statusHexMap[status] || '#5C5C72'
}

const severityColorMap = {
  P1: '#FF5C5C',
  P2: '#FFB547',
  P3: '#3B9EFF',
  P4: '#5C5C72',
  critical: '#FF5C5C',
  high: '#FFB547',
  medium: '#3B9EFF',
  low: '#5C5C72',
}

export function getSeverityColor(severity) {
  return severityColorMap[severity] || '#5C5C72'
}

const laneColorMap = {
  control: '#7C5CFC',
  value: '#00E5A0',
  support: '#FFB547',
  delivery: '#3B9EFF',
}

export function getLaneColor(lane) {
  return laneColorMap[lane] || '#5C5C72'
}

export function getRiskColor(riskLevel) {
  switch (riskLevel) {
    case 'high_risk': return '#FF5C5C'
    case 'critical': return '#FF5C5C'
    case 'watch': return '#FFB547'
    case 'healthy': return '#00E5A0'
    default: return '#5C5C72'
  }
}

const eventTypeColorMap = {
  jira_ticket_created: '#7C5CFC',
  fathom_call_processed: '#3B9EFF',
  zoom_call_completed: '#3B9EFF',
  daily_health_check: '#00E5A0',
  health_check: '#00E5A0',
  new_alert: '#FFB547',
  alert_fired: '#FF5C5C',
}

export function getEventTypeColor(eventType) {
  return eventTypeColorMap[eventType] || '#7C5CFC'
}
