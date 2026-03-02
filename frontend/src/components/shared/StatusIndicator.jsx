import { cn } from '../../utils/cn'
import { getStatusHex } from '../../utils/formatters'

export default function StatusIndicator({ status = 'idle', size = 'md', showLabel = false }) {
  const color = getStatusHex(status)
  const shouldPulse = status === 'active' || status === 'processing'
  const dotSize = size === 'sm' ? 6 : size === 'lg' ? 10 : 8

  return (
    <div data-testid="status-indicator" className="flex items-center gap-2">
      <span className="relative flex items-center justify-center" style={{ width: dotSize + 4, height: dotSize + 4 }}>
        {shouldPulse && (
          <span
            className="absolute rounded-full animate-ping"
            style={{
              width: dotSize,
              height: dotSize,
              backgroundColor: color,
              opacity: 0.3,
            }}
          />
        )}
        <span
          className="relative rounded-full"
          style={{
            width: dotSize,
            height: dotSize,
            backgroundColor: color,
          }}
        />
      </span>
      {showLabel && (
        <span
          className={cn('font-mono text-xs font-medium capitalize')}
          style={{ color }}
        >
          {status.replace('_', ' ')}
        </span>
      )}
    </div>
  )
}
