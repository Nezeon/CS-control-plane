export function isWebGLAvailable() {
  try {
    const canvas = document.createElement('canvas')
    return !!(canvas.getContext('webgl2') || canvas.getContext('webgl'))
  } catch {
    return false
  }
}

export function shouldUse3D(minWidth = 1024) {
  if (typeof window === 'undefined') return false
  if (!isWebGLAvailable()) return false
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return false
  if (document.documentElement.classList.contains('reduce-motion')) return false
  if (window.innerWidth < minWidth) return false
  return true
}
