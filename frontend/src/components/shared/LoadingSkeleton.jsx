import { cn } from '../../utils/cn'

const variantClasses = {
  text: 'h-4 w-full rounded',
  circle: 'rounded-full',
  rect: 'rounded-lg',
  card: 'h-32 w-full rounded-xl',
}

export default function LoadingSkeleton({ variant = 'text', width, height, className, count = 1 }) {
  const items = Array.from({ length: count }, (_, i) => i)

  return (
    <div data-testid="loading-skeleton" className={cn(count > 1 && 'flex flex-col gap-2')}>
      {items.map((i) => (
        <div
          key={i}
          className={cn('skeleton', variantClasses[variant], className)}
          style={{
            width: width || undefined,
            height: height || undefined,
          }}
        />
      ))}
    </div>
  )
}
