import { cn } from '../../utils/cn'

const variantClasses = {
  text: 'h-3 rounded',
  card: 'h-32 w-full rounded-xl',
  circle: 'rounded-full',
  chart: 'h-48 w-full rounded-xl',
}

const textWidths = ['w-full', 'w-3/4', 'w-5/6', 'w-2/3', 'w-4/5']

export default function LoadingSkeleton({ variant = 'text', count = 1, className }) {
  const items = Array.from({ length: count }, (_, i) => i)

  return (
    <div className={cn(count > 1 && 'flex flex-col gap-3')}>
      {items.map((i) => {
        const isText = variant === 'text'
        const isCircle = variant === 'circle'

        return (
          <div
            key={`skeleton-${i}`}
            className={cn(
              'skeleton',
              variantClasses[variant] || variantClasses.text,
              isText && textWidths[i % textWidths.length],
              isCircle && 'w-10 h-10',
              className
            )}
          />
        )
      })}
    </div>
  )
}
