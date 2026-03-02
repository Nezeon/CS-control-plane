import { useRef, useState, useEffect } from 'react'

/**
 * IntersectionObserver hook for scroll-reveal animations.
 * Returns [ref, isVisible].
 *
 * Options:
 *   threshold — 0..1 visibility fraction (default 0.15)
 *   rootMargin — observer margin (default '-60px')
 *   once — fire only once (default true)
 */
export default function useScrollReveal({ threshold = 0.15, rootMargin = '-60px', once = true } = {}) {
  const ref = useRef(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    // Respect reduced-motion: immediately set visible
    const reducedMotion =
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ||
      document.documentElement.classList.contains('reduce-motion')

    if (reducedMotion) {
      setIsVisible(true)
      return
    }

    const el = ref.current
    if (!el) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          if (once) observer.unobserve(el)
        } else if (!once) {
          setIsVisible(false)
        }
      },
      { threshold, rootMargin }
    )

    observer.observe(el)
    return () => observer.disconnect()
  }, [threshold, rootMargin, once])

  return [ref, isVisible]
}
