import { cn } from '../../utils/cn'

export default function SurfaceCard({ elevated = false, interactive = false, className, children, onClick, ...rest }) {
  return (
    <div
      className={cn(
        elevated ? 'card-elevated' : 'card',
        interactive && 'card-interactive',
        className
      )}
      onClick={onClick}
      {...rest}
    >
      {children}
    </div>
  )
}
