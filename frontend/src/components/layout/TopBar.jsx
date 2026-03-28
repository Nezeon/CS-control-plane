import { useState, useEffect } from 'react'
import { Bell } from 'lucide-react'
import api from '../../services/api'

export default function TopBar({ title, onBellClick }) {
  const [alertCount, setAlertCount] = useState(0)

  useEffect(() => {
    api.get('/alerts', { params: { status: 'open', limit: 1 } })
      .then(({ data }) => setAlertCount(data?.total ?? 0))
      .catch(() => {})
  }, [])

  return (
    <header
      className="flex items-center justify-between px-6 border-b flex-shrink-0"
      style={{
        height: 45,
        background: 'var(--bg-paper)',
        borderColor: 'var(--border)',
      }}
    >
      <h1 className="text-base font-medium" style={{ color: 'var(--text-primary)' }}>
        {title}
      </h1>

      <div className="flex items-center gap-4">
        <button
          onClick={onBellClick}
          className="relative cursor-pointer p-1 rounded-md transition-colors duration-150"
          style={{ color: 'var(--text-secondary)' }}
        >
          <Bell size={18} />
          {alertCount > 0 && (
            <span
              className="absolute -top-1 -right-1 w-4 h-4 rounded-full text-[10px] font-medium flex items-center justify-center"
              style={{ background: 'var(--error)', color: '#FFFFFF' }}
            >
              {alertCount > 9 ? '9+' : alertCount}
            </span>
          )}
        </button>
      </div>
    </header>
  )
}
