import { cn } from '../../utils/cn'

const tierConfig = {
  1: { bg: 'bg-tier-1/10', text: 'text-tier-1', label: 'T1' },
  2: { bg: 'bg-tier-2/10', text: 'text-tier-2', label: 'T2' },
  3: { bg: 'bg-tier-3/10', text: 'text-tier-3', label: 'T3' },
  4: { bg: 'bg-tier-4/10', text: 'text-tier-4', label: 'T4' },
}

export default function TierBadge({ tier = 3, label, className }) {
  const config = tierConfig[tier] || tierConfig[3]

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5',
        'text-xxs font-medium font-mono',
        config.bg,
        config.text,
        className
      )}
    >
      {config.label}
      {label && (
        <>
          <span className="opacity-40">&middot;</span>
          {label}
        </>
      )}
    </span>
  )
}
