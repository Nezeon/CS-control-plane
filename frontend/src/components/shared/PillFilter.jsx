import { cn } from '../../utils/cn'

export default function PillFilter({ options = [], value, onChange, className }) {
  return (
    <div className={cn('flex flex-wrap items-center gap-2', className)}>
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          className={cn('pill', value === opt.value && 'pill-active')}
          onClick={() => onChange?.(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
