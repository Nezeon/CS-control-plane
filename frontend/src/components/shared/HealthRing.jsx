import { useEffect, useState, useId } from 'react'

function getColor(score) {
  if (score >= 80) return '#00E5C4'
  if (score >= 60) return '#3B9EFF'
  if (score >= 40) return '#FFB547'
  return '#FF5C5C'
}

export default function HealthRing({ score = 0, size = 48, strokeWidth = 4 }) {
  const id = useId()
  const s = Math.min(Math.max(score, 0), 100)
  const r = (size - strokeWidth * 2) / 2
  const circ = 2 * Math.PI * r
  const target = circ * (1 - s / 100)
  const cx = size / 2

  const [offset, setOffset] = useState(circ)
  useEffect(() => {
    const t = setTimeout(() => setOffset(target), 50)
    return () => clearTimeout(t)
  }, [target])

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle cx={cx} cy={cx} r={r} fill="none" stroke="var(--border)" strokeWidth={strokeWidth} />
        <circle
          cx={cx} cy={cx} r={r} fill="none"
          stroke={getColor(s)} strokeWidth={strokeWidth} strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset}
          transform={`rotate(-90 ${cx} ${cx})`}
          style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
        />
      </svg>
      <span className="absolute font-display font-bold text-[var(--text-primary)]" style={{ fontSize: size * 0.28 }}>
        {Math.round(s)}
      </span>
    </div>
  )
}
