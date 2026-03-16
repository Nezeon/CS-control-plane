import { forwardRef } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '../../utils/cn'

const sizeClasses = {
  sm: 'px-3 py-1.5 text-xs rounded-lg gap-1.5',
  md: 'px-5 py-2.5 text-sm rounded-xl gap-2',
  lg: 'px-6 py-3 text-base rounded-xl gap-2',
}

const GradientButton = forwardRef(function GradientButton(
  { children, onClick, disabled = false, size = 'md', className, icon: Icon, loading = false, ...rest },
  ref
) {
  return (
    <button
      ref={ref}
      type="button"
      className={cn(
        'btn-gradient inline-flex items-center justify-center font-semibold',
        sizeClasses[size] || sizeClasses.md,
        (disabled || loading) && 'opacity-50 cursor-not-allowed pointer-events-none',
        className
      )}
      onClick={onClick}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? (
        <Loader2 size={size === 'sm' ? 14 : 16} className="animate-spin" />
      ) : (
        <>
          {Icon && <Icon size={size === 'sm' ? 14 : 16} className="flex-shrink-0" />}
          {children}
        </>
      )}
    </button>
  )
})

export default GradientButton
