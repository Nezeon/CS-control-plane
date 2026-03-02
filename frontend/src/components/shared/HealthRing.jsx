import { useEffect, useState } from 'react'
import { cn } from '../../utils/cn'

const sizeMap = {
  sm: { px: 40, stroke: 3, fontSize: 'text-xs' },
  md: { px: 56, stroke: 3.5, fontSize: 'text-base' },
  lg: { px: 80, stroke: 4, fontSize: 'text-xl' },
}

function getScoreColor(score) {
  if (score >= 70) return '#22C55E'
  if (score >= 40) return '#EAB308'
  return '#EF4444'
}

export default function HealthRing({ score = 0, size = 'md', animate = true, showLabel = true, className }) {
  const { px, stroke, fontSize } = sizeMap[size] || sizeMap.md
  const radius = (px - stroke * 2) / 2
  const circumference = 2 * Math.PI * radius
  const target = circumference * (1 - Math.min(Math.max(score, 0), 100) / 100)
  const [offset, setOffset] = useState(animate ? circumference : target)
  const color = getScoreColor(score)

  useEffect(() => {
    if (!animate) {
      setOffset(target)
      return
    }
    setOffset(circumference)
    const timeout = setTimeout(() => setOffset(target), 50)
    return () => clearTimeout(timeout)
  }, [score, animate, circumference, target])

  return (
    <div data-testid="health-ring" className={cn('relative inline-flex items-center justify-center', className)} style={{ width: px, height: px }}>
      <svg width={px} height={px} viewBox={`0 0 ${px} ${px}`}>
        <circle
          cx={px / 2}
          cy={px / 2}
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth={stroke}
        />
        <circle
          cx={px / 2}
          cy={px / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${px / 2} ${px / 2})`}
          style={{
            transition: animate ? 'stroke-dashoffset 1.2s ease-out' : 'none',
          }}
        />
      </svg>
      {showLabel && (
        <span className={cn('absolute font-semibold text-text-primary tabular-nums', fontSize)}>
          {Math.round(score)}
        </span>
      )}
    </div>
  )
}
