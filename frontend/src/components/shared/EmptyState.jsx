export default function EmptyState({ icon: Icon, title, description, actionLabel, onAction }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {Icon && (
        <div
          className="w-12 h-12 rounded-lg flex items-center justify-center mb-4"
          style={{ background: 'color-mix(in srgb, var(--primary) 15%, transparent)' }}
        >
          <Icon size={24} style={{ color: 'var(--primary)' }} />
        </div>
      )}
      <h3 className="text-base font-medium mb-1" style={{ color: 'var(--text-primary)' }}>
        {title}
      </h3>
      {description && (
        <p className="text-sm max-w-sm" style={{ color: 'var(--text-secondary)' }}>
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="mt-4 px-4 py-2 text-sm font-medium cursor-pointer transition-colors duration-150"
          style={{
            background: 'var(--primary)',
            color: 'var(--primary-contrast)',
            borderRadius: 30,
          }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}
