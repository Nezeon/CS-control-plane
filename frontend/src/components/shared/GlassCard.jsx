const LEVELS = { near: 'glass-near', mid: 'glass-mid', far: 'glass-far' }

export default function GlassCard({ children, level = 'near', className = '', ...rest }) {
  return (
    <div className={`${LEVELS[level] || LEVELS.near} p-4 ${className}`} {...rest}>
      {children}
    </div>
  )
}
