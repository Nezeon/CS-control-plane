import * as d3 from 'd3'
import { getLaneColor } from './formatters'

/* ─── Color constants — Obsidian Luxe palette ─── */

export const SEVERITY_COLORS = {
  P1: '#FF5C5C',
  P2: '#FFB547',
  P3: '#3B9EFF',
  P4: '#5C5C72',
  critical: '#FF5C5C',
  high: '#FFB547',
  medium: '#3B9EFF',
  low: '#5C5C72',
}

export const SENTIMENT_COLORS = {
  positive: '#00E5A0',
  neutral: '#5C5C72',
  negative: '#FF5C5C',
}

export const AGENT_LANE_MAP = {
  cs_orchestrator: 'control',
  orchestrator: 'control',
  memory_agent: 'control',
  health_monitor: 'control',
  escalation_agent: 'control',
  fathom: 'value',
  fathom_agent: 'value',
  qbr_generator: 'value',
  qbr_prep: 'value',
  ticket_triage: 'support',
  troubleshooter: 'support',
  sow_analyzer: 'delivery',
  sow_tracker: 'delivery',
  deployment_intel: 'delivery',
  deploy_onboard: 'delivery',
  renewal_forecaster: 'value',
  escalation_drafter: 'value',
}

/* ─── Health color scale ─── */

const healthInterpolator = d3.interpolateRgbBasis(['#FF5C5C', '#FFB547', '#00E5A0'])
const _healthScale = d3.scaleSequential([0, 100], healthInterpolator)

export function healthColorScale(score) {
  if (score == null) return '#27272A'
  return _healthScale(Math.max(0, Math.min(100, score)))
}

/* ─── Cross-filter matching ─── */

export function getCrossFilterOpacity(crossFilter, datum, chartSource) {
  if (!crossFilter) return 1
  if (crossFilter.source === chartSource) return 1

  const { type, value } = crossFilter

  switch (chartSource) {
    case 'heatmap': {
      if (type === 'customer') return datum.customer_name === value ? 1 : 0.2
      if (type === 'date') return datum.date === value ? 1 : 0.2
      return 1
    }
    case 'velocity': {
      if (type === 'severity') return datum.severity === value ? 1 : 0.2
      if (type === 'date') return datum.week === value ? 1 : 0.2
      return 1
    }
    case 'river': {
      if (type === 'date') return datum.date === value ? 1 : 0.2
      return 1
    }
    case 'throughput': {
      if (type === 'agent') return datum.agent === value ? 1 : 0.2
      return 1
    }
    default:
      return 1
  }
}

/* ─── Get agent lane color ─── */

export function getAgentLaneColor(agentName) {
  const key = agentName?.toLowerCase().replace(/\s+/g, '_')
  const lane = AGENT_LANE_MAP[key]
  return lane ? getLaneColor(lane) : '#71717A'
}

/* ─── Debounce utility ─── */

export function debounce(fn, ms) {
  let timer
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), ms)
  }
}
