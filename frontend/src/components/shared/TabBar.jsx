import { m } from 'framer-motion'
import { cn } from '../../utils/cn'

export default function TabBar({ tabs = [], activeTab, onTabChange, className }) {
  return (
    <div className={cn('tab-bar', className)}>
      {tabs.map((tab) => {
        const isActive = tab.key === activeTab
        const Icon = tab.icon

        return (
          <button
            key={tab.key}
            type="button"
            className={cn('tab-item relative', isActive && 'tab-item-active')}
            onClick={() => onTabChange?.(tab.key)}
          >
            {isActive && (
              <m.div
                layoutId="tab-indicator"
                className="absolute inset-0 rounded-lg bg-bg-card"
                style={{ zIndex: -1 }}
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative z-10 inline-flex items-center gap-1.5">
              {Icon && <Icon size={14} className="flex-shrink-0" />}
              {tab.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}
