import { useEffect, useState, useId } from 'react'
import { cn } from '../../utils/cn'

const SIZE_MAP = { sm: 28, md: 48, lg: 64 }

function getScoreColor(score) {
  if (score >= 80) return { start: '#00E5C4', end: '#00B89E' }
  if (score >= 60) return { start: '#3B9EFF', end: '#2B7BD4' }
  if (score >= 40) return { start: '#FFB547', end: '#E09A2F' }
  return { start: '#FF5C5C', end: '#D94444' }
}

export default function HealthRing({ score = 0, size = 64, strokeWidth = 4, className }) {
  const id = useId()
  const gradientId = `health-grad-${id}`
  const glowId = `health-glow-${id}`

  const resolvedSize = typeof size === 'string' ? SIZE_MAP[size] || 64 : size
  const clampedScore = Math.min(Math.max(score, 0), 100)
  const radius = (resolvedSize - strokeWidth * 2) / 2
  const circumference = 2 * Math.PI * radius
  const target = circumference * (1 - clampedScore / 100)
  const center = resolvedSize / 2

  const [offset, setOffset] = useState(circumference)
  const colors = getScoreColor(clampedScore)

  useEffect(() => {
    // Delay to trigger CSS transition on mount
    const timeout = setTimeout(() => setOffset(target), 50)
    return () => clearTimeout(timeout)
  }, [target])

  return (
    <div
      className={cn('relative inline-flex items-center justify-center', className)}
      style={{ width: resolvedSize, height: resolvedSize }}
    >
      <svg width={resolvedSize} height={resolvedSize} viewBox={`0 0 ${resolvedSize} ${resolvedSize}`}>
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={colors.start} />
            <stop offset="100%" stopColor={colors.end} />
          </linearGradient>
          <filter id={glowId}>
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Track */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth={strokeWidth}
        />

        {/* Progress arc */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${center} ${center})`}
          filter={`url(#${glowId})`}
          style={{
            transition: 'stroke-dashoffset 1.2s ease-out',
          }}
        />
      </svg>

      {/* Center score */}
      <span className="absolute font-display font-bold text-text-primary" style={{ fontSize: resolvedSize * 0.28 }}>
        {Math.round(clampedScore)}
      </span>
    </div>
  )
}
