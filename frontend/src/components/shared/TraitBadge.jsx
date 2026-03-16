import { cn } from '../../utils/cn'

function formatTrait(trait) {
  if (!trait) return ''
  const words = trait.replace(/_/g, ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

export default function TraitBadge({ trait, className }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5',
        'text-xxs font-medium',
        'bg-bg-hover text-text-muted border border-border-subtle',
        className
      )}
    >
      {formatTrait(trait)}
    </span>
  )
}
