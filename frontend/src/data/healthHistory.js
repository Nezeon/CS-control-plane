// Seed: Per-customer 30-day health history arrays
// Deterministic trends — Acme trends down (60→42), Beta trends up (78→88), etc.

const NOW = Date.now()
const DAY = 86400000
const mkDate = (daysAgo) => new Date(NOW - daysAgo * DAY).toISOString().split('T')[0]

function generateHistory(startHealth, endHealth, volatility, seed) {
  return Array.from({ length: 30 }, (_, i) => {
    const t = i / 29
    const base = startHealth + (endHealth - startHealth) * t
    const wobble = volatility * Math.sin(i * 0.5 + seed * 0.1)
    return {
      date: mkDate(29 - i),
      score: Math.round(Math.max(0, Math.min(100, base + wobble))),
    }
  })
}

export const seedHealthHistory = {
  'cust-001': generateHistory(60, 42, 3, 60),   // Acme — trending down
  'cust-002': generateHistory(78, 88, 2, 78),   // Beta — trending up
  'cust-003': generateHistory(50, 55, 4, 50),   // Gamma — slow improvement
  'cust-004': generateHistory(89, 91, 1, 89),   // Delta — stable high
  'cust-005': generateHistory(55, 38, 5, 55),   // Epsilon — sharp decline
  'cust-006': generateHistory(72, 67, 3, 72),   // Zeta — mild decline
  'cust-007': generateHistory(80, 85, 2, 80),   // Eta — steady improvement
  'cust-008': generateHistory(78, 72, 3, 78),   // Theta — mild decline
  'cust-009': generateHistory(56, 44, 4, 56),   // Iota — declining
  'cust-010': generateHistory(54, 60, 3, 54),   // Kappa — improving
}
