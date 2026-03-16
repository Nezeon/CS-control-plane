import { useMemo } from 'react'
import PillFilter from '../shared/PillFilter'
import MemoryEntry from './MemoryEntry'

const laneOptions = [
  { value: 'all', label: 'All Lanes' },
  { value: 'support', label: 'Support' },
  { value: 'value', label: 'Value' },
  { value: 'delivery', label: 'Delivery' },
]

export default function KnowledgePool({ entries, selectedLane, onLaneChange }) {
  const filteredEntries = useMemo(() => {
    if (!entries) return []
    if (selectedLane === 'all') return entries
    return entries.filter((e) => e.lane === selectedLane)
  }, [entries, selectedLane])

  return (
    <div className="space-y-4">
      {/* Lane filter */}
      <PillFilter options={laneOptions} value={selectedLane} onChange={onLaneChange} />

      {/* Knowledge grid */}
      {filteredEntries.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-xs text-text-ghost">No knowledge entries for this lane</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {filteredEntries
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .map((entry) => (
              <MemoryEntry key={entry.id} entry={entry} variant="knowledge" />
            ))}
        </div>
      )}
    </div>
  )
}
