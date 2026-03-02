import { useEffect, useRef, useState } from 'react'
import { cn } from '../../utils/cn'

export default function AnimatedCounter({ value = 0, duration = 1200, prefix = '', suffix = '', className }) {
  const [display, setDisplay] = useState(value)
  const rafRef = useRef(null)
  const startRef = useRef(null)
  const fromRef = useRef(0)
  const reducedMotion = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  useEffect(() => {
    if (reducedMotion) {
      setDisplay(value)
      return
    }

    fromRef.current = display
    startRef.current = performance.now()

    function animate(now) {
      const elapsed = now - startRef.current
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = Math.round(fromRef.current + (value - fromRef.current) * eased)
      setDisplay(current)

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate)
      }
    }

    rafRef.current = requestAnimationFrame(animate)
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [value, duration, reducedMotion])

  return (
    <span data-testid="animated-counter" className={cn('font-semibold text-text-primary tabular-nums', className)}>
      {prefix}{typeof display === 'number' ? Math.round(display).toLocaleString() : display}{suffix}
    </span>
  )
}
