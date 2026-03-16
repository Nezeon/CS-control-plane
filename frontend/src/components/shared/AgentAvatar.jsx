import { cn } from '../../utils/cn'

const tierColors = {
  1: { border: 'border-tier-1', glow: 'shadow-[0_0_8px_rgba(124,92,252,0.4)]' },
  2: { border: 'border-tier-2', glow: 'shadow-[0_0_8px_rgba(59,158,255,0.4)]' },
  3: { border: 'border-tier-3', glow: 'shadow-[0_0_8px_rgba(0,229,196,0.4)]' },
  4: { border: 'border-tier-4', glow: '' },
}

const sizeClasses = {
  sm: 'w-6 h-6 text-xxs',
  md: 'w-9 h-9 text-xs',
  lg: 'w-12 h-12 text-sm',
}

export default function AgentAvatar({ name = '', tier = 3, size = 'md', status = 'idle', className }) {
  const initial = name.charAt(0).toUpperCase() || '?'
  const tierConfig = tierColors[tier] || tierColors[3]
  const isActive = status === 'active' || status === 'processing'

  return (
    <div
      className={cn(
        'relative inline-flex items-center justify-center rounded-full',
        'bg-bg-active font-display font-semibold text-text-primary',
        'border-2',
        tierConfig.border,
        sizeClasses[size] || sizeClasses.md,
        isActive && tierConfig.glow,
        status === 'processing' && 'animate-pulse-subtle',
        className
      )}
      title={name}
    >
      {initial}
    </div>
  )
}
