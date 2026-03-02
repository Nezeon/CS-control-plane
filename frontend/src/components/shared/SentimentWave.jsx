import { useEffect, useRef, useMemo } from 'react'

const sentimentColorMap = {
  positive: '#22C55E',
  neutral: '#52525B',
  negative: '#EF4444',
}

export default function SentimentWave({ sentiment = 'neutral', intensity = 0.5 }) {
  const pathRef = useRef(null)
  const color = sentimentColorMap[sentiment] || sentimentColorMap.neutral
  const amp = 3 + intensity * 4

  const d = useMemo(() => {
    const points = []
    const segments = 5
    for (let i = 0; i <= segments; i++) {
      const x = (i / segments) * 40
      const y = 8 + Math.sin(i * 1.8 + Math.random() * 0.5) * amp * (0.5 + Math.random() * 0.5)
      points.push({ x, y })
    }
    let path = `M ${points[0].x} ${points[0].y}`
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1]
      const curr = points[i]
      const cpx = (prev.x + curr.x) / 2
      path += ` Q ${cpx} ${prev.y} ${curr.x} ${curr.y}`
    }
    return path
  }, [sentiment, intensity, amp])

  useEffect(() => {
    const el = pathRef.current
    if (!el) return
    const length = el.getTotalLength()
    el.style.strokeDasharray = length
    el.style.strokeDashoffset = length
    requestAnimationFrame(() => {
      el.style.transition = 'stroke-dashoffset 0.6s ease-out'
      el.style.strokeDashoffset = '0'
    })
  }, [d])

  return (
    <svg data-testid="sentiment-wave" width={40} height={16} viewBox="0 0 40 16" className="flex-shrink-0">
      <path
        ref={pathRef}
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        opacity={0.8}
      />
    </svg>
  )
}
