import { useMemo } from 'react'
import { cn } from '../../utils/cn'
import { AGENT_NAMES } from '../../data/conversations'
import MemoryEntry from './MemoryEntry'

const agentOptions = [
  { value: 'all', label: 'All Agents' },
  { value: 'triage_agent', label: 'Kai Nakamura' },
  { value: 'troubleshooter_agent', label: 'Leo Petrov' },
  { value: 'escalation_agent', label: 'Maya Santiago' },
  { value: 'health_monitor_agent', label: 'Dr. Aisha Okafor' },
  { value: 'fathom_agent', label: 'Jordan Ellis' },
  { value: 'qbr_agent', label: 'Sofia Marquez' },
  { value: 'sow_agent', label: 'Ethan Brooks' },
  { value: 'deployment_intel_agent', label: 'Zara Kim' },
  { value: 'customer_memory', label: 'Atlas' },
  { value: 'cso_orchestrator', label: 'Naveen Kapoor' },
  { value: 'support_lead', label: 'Rachel Torres' },
  { value: 'value_lead', label: 'Damon Reeves' },
  { value: 'delivery_lead', label: 'Priya Mehta' },
]

export default function EpisodicTimeline({ memories, selectedAgent, onAgentChange }) {
  const filteredMemories = useMemo(() => {
    if (!memories) return []
    if (selectedAgent === 'all') return memories
    return memories.filter((m) => m.agent_id === selectedAgent)
  }, [memories, selectedAgent])

  return (
    <div className="space-y-4">
      {/* Agent selector */}
      <div>
        <label className="text-xxs font-mono text-text-ghost uppercase tracking-wider block mb-1.5">
          Agent
        </label>
        <select
          value={selectedAgent}
          onChange={(e) => onAgentChange(e.target.value)}
          className={cn(
            'w-full max-w-xs rounded-lg px-3 py-2 text-sm',
            'bg-bg-subtle border border-border-subtle text-text-secondary',
            'focus:outline-none focus:border-accent/30 transition-colors'
          )}
        >
          {agentOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Vertical timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-px bg-border-subtle" />

        <div className="space-y-3 pl-8">
          {filteredMemories.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-xs text-text-ghost">
                No episodic memories for {selectedAgent === 'all' ? 'any agent' : AGENT_NAMES[selectedAgent] || selectedAgent}
              </p>
            </div>
          ) : (
            filteredMemories
              .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
              .map((memory) => (
                <div key={memory.id} className="relative">
                  {/* Timeline dot */}
                  <div
                    className={cn(
                      'absolute -left-8 top-4 w-2 h-2 rounded-full',
                      memory.importance >= 8 ? 'bg-status-danger' : memory.importance >= 5 ? 'bg-status-warning' : 'bg-teal'
                    )}
                    style={{ transform: 'translateX(-50%)' }}
                  />
                  <MemoryEntry entry={memory} variant="episodic" />
                </div>
              ))
          )}
        </div>
      </div>
    </div>
  )
}
