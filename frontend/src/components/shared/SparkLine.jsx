import { useMemo } from 'react'
import { cn } from '../../utils/cn'

export default function SparkLine({ data = [], width = 80, height = 24, color = '#7C5CFC', className }) {
  const { points, fillPoints } = useMemo(() => {
    if (!data || data.length < 2) return { points: '', fillPoints: '' }

    const min = Math.min(...data)
    const max = Math.max(...data)
    const range = max - min || 1
    const stepX = width / (data.length - 1)
    const padding = 2

    const coords = data.map((v, i) => {
      const x = i * stepX
      const y = padding + (1 - (v - min) / range) * (height - padding * 2)
      return `${x},${y}`
    })

    const linePoints = coords.join(' ')
    const fill = `0,${height} ${linePoints} ${width},${height}`

    return { points: linePoints, fillPoints: fill }
  }, [data, width, height])

  if (!data || data.length < 2) return null

  const gradientId = `spark-fill-${color.replace('#', '')}`

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={cn('overflow-visible', className)}
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={fillPoints} fill={`url(#${gradientId})`} />
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
