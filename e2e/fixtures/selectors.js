/**
 * Centralized test selectors matching data-testid attributes.
 * Organized by section for easy reference.
 */

export const SELECTORS = {
  // Layout
  mainContent: '[data-testid="main-content"]',
  topBar: '[data-testid="top-bar"]',
  breadcrumb: '[data-testid="breadcrumb"]',
  orbitalNav: '[data-testid="orbital-nav"]',
  mobileNav: '[data-testid="mobile-nav"]',
  commandPalette: '[data-testid="command-palette"]',
  commandPaletteInput: '[data-testid="command-palette-input"]',
  commandPaletteResults: '[data-testid="command-palette-results"]',
  wsIndicator: '[data-testid="ws-indicator"]',
  logoutButton: '[data-testid="logout-button"]',

  // Login
  loginPage: '[data-testid="login-page"]',
  loginEmail: '[data-testid="login-email"]',
  loginPassword: '[data-testid="login-password"]',
  loginSubmit: '[data-testid="login-submit"]',
  loginError: '[data-testid="login-error"]',

  // Dashboard
  dashboardPage: '[data-testid="dashboard-page"]',
  floatingOrbsGrid: '[data-testid="floating-orbs-grid"]',
  neuralSphere: '[data-testid="neural-sphere"]',
  dataFlowRivers: '[data-testid="data-flow-rivers"]',
  healthTerrain: '[data-testid="health-terrain"]',
  livePulse: '[data-testid="live-pulse"]',
  quickActions: '[data-testid="quick-actions"]',

  // Customers
  customersPage: '[data-testid="customers-page"]',
  customersSearch: '[data-testid="customers-search"]',
  customersRiskFilter: '[data-testid="customers-risk-filter"]',
  customersTierFilter: '[data-testid="customers-tier-filter"]',
  customersSort: '[data-testid="customers-sort"]',
  premiumGrid: '[data-testid="premium-grid"]',
  customerDataTable: '[data-testid="customer-data-table"]',
  solarSystemView: '[data-testid="solar-system-view"]',
  quickIntelPanel: '[data-testid="quick-intel-panel"]',

  // Customer Detail
  customerDetailPage: '[data-testid="customer-detail-page"]',
  customerNotFound: '[data-testid="customer-not-found"]',
  customerHero: '[data-testid="customer-hero"]',
  healthStory: '[data-testid="health-story"]',
  deploymentDna: '[data-testid="deployment-dna"]',
  customerJourney: '[data-testid="customer-journey"]',
  intelPanels: '[data-testid="intel-panels"]',

  // Agents
  agentsPage: '[data-testid="agents-page"]',
  neuralNetwork: '[data-testid="neural-network"]',
  agentBrainPanel: '[data-testid="agent-brain-panel"]',
  reasoningLog: '[data-testid="reasoning-log"]',

  // Insights
  insightsPage: '[data-testid="insights-page"]',
  insightsSearch: '[data-testid="insights-search"]',
  sentimentSpectrum: '[data-testid="sentiment-spectrum"]',
  insightCard: '[data-testid="insight-card"]',
  actionTracker: '[data-testid="action-tracker"]',

  // Tickets
  ticketsPage: '[data-testid="tickets-page"]',
  ticketsSearch: '[data-testid="tickets-search"]',
  ticketsStatusFilter: '[data-testid="tickets-status-filter"]',
  ticketsSeverityFilter: '[data-testid="tickets-severity-filter"]',
  warroomTable: '[data-testid="warroom-table"]',
  ticketConstellation: '[data-testid="ticket-constellation"]',
  ticketDetailDrawer: '[data-testid="ticket-detail-drawer"]',

  // Reports
  reportsPage: '[data-testid="reports-page"]',
  healthHeatmap: '[data-testid="health-heatmap"]',
  ticketVelocity: '[data-testid="ticket-velocity"]',
  sentimentRiver: '[data-testid="sentiment-river"]',
  agentThroughput: '[data-testid="agent-throughput"]',
  crossFilterPill: '[data-testid="cross-filter-pill"]',
  reportList: '[data-testid="report-list"]',

  // Settings
  settingsPage: '[data-testid="settings-page"]',
  reduceMotionToggle: '[data-testid="reduce-motion-toggle"]',

  // Shared
  loadingSkeleton: '[data-testid="loading-skeleton"]',
  emptyState: '[data-testid="empty-state"]',
  healthRing: '[data-testid="health-ring"]',
  severityMarker: '[data-testid="severity-marker"]',
  statusIndicator: '[data-testid="status-indicator"]',
}

/**
 * Orbital Nav items by route name.
 */
export const NAV_ITEMS = {
  dashboard: '[data-testid="orbital-nav-item-dashboard"]',
  customers: '[data-testid="orbital-nav-item-customers"]',
  agents: '[data-testid="orbital-nav-item-agents"]',
  insights: '[data-testid="orbital-nav-item-insights"]',
  tickets: '[data-testid="orbital-nav-item-tickets"]',
  reports: '[data-testid="orbital-nav-item-reports"]',
  settings: '[data-testid="orbital-nav-item-settings"]',
}
