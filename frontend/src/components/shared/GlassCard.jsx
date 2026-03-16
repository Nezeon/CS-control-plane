import { forwardRef } from 'react'
import { cn } from '../../utils/cn'

const levelClasses = {
  near: 'glass-near',
  mid: 'glass-mid',
  far: 'glass-far',
}

const GlassCard = forwardRef(function GlassCard(
  { children, level = 'near', interactive = false, className, onClick, ...rest },
  ref
) {
  return (
    <div
      ref={ref}
      className={cn(
        levelClasses[level] || levelClasses.near,
        interactive && 'glass-interactive',
        'p-4',
        className
      )}
      onClick={onClick}
      {...rest}
    >
      {children}
    </div>
  )
})

export default GlassCard
