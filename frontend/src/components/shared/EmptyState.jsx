import { cn } from '../../utils/cn'
import { Inbox } from 'lucide-react'

export default function EmptyState({
  title = 'No data available',
  subtitle = '',
  icon: Icon = Inbox,
  action = null,
  className,
}) {
  return (
    <div data-testid="empty-state" className={cn('flex flex-col items-center justify-center py-16 px-4', className)}>
      <div className="w-12 h-12 rounded-xl bg-bg-active flex items-center justify-center mb-4">
        <Icon className="w-5 h-5 text-text-ghost" />
      </div>
      <p className="text-sm font-medium text-text-muted">{title}</p>
      {subtitle && <p className="text-xs text-text-ghost mt-1">{subtitle}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
