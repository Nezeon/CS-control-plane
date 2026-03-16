import { useMemo } from 'react'
import { Search } from 'lucide-react'
import { cn } from '../../utils/cn'
import GlassCard from '../shared/GlassCard'
import { AGENT_TIERS } from '../../data/conversations'
import AgentAvatar from '../shared/AgentAvatar'
import { formatRelativeTime } from '../../utils/formatters'

function SearchResult({ item }) {
  const isEpisodic = item.type === 'episodic'
  const agentName = isEpisodic ? item.agent_name : item.published_by_name
  const agentId = isEpisodic ? item.agent_id : item.published_by
  const tier = AGENT_TIERS[agentId] || 3
  const content = item.summary || item.content || ''
  const tags = item.tags || []

  return (
    <GlassCard level="near" className="p-3.5">
      <div className="flex items-start gap-3">
        <AgentAvatar name={agentName || ''} tier={tier} size="sm" className="mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span
              className={cn(
                'px-1.5 py-0.5 rounded text-xxs font-mono',
                isEpisodic ? 'bg-accent-subtle text-accent' : 'bg-teal-subtle text-teal'
              )}
            >
              {isEpisodic ? 'episodic' : 'knowledge'}
            </span>
            <span className="text-sm font-medium text-text-primary">{agentName}</span>
            {!isEpisodic && item.lane && (
              <span className="text-xxs text-text-ghost font-mono">{item.lane} lane</span>
            )}
            {isEpisodic && item.customer_name && (
              <span className="text-xxs text-text-ghost font-mono">{item.customer_name}</span>
            )}
            <span className="text-xxs text-text-ghost ml-auto shrink-0">
              {formatRelativeTime(item.created_at)}
            </span>
          </div>

          {/* Content */}
          <p className="text-xs text-text-secondary leading-relaxed mb-2">
            {content}
          </p>

          {/* Tags */}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {tags.slice(0, 6).map((tag) => (
                <span
                  key={tag}
                  className="px-1.5 py-0.5 rounded text-xxs font-mono bg-bg-active text-text-muted border border-border-subtle"
                >
                  {tag}
                </span>
              ))}
              {tags.length > 6 && (
                <span className="text-xxs text-text-ghost">+{tags.length - 6} more</span>
              )}
            </div>
          )}
        </div>
      </div>
    </GlassCard>
  )
}

export default function MemorySearch({ allItems, searchQuery, onSearchChange }) {
  const results = useMemo(() => {
    if (!searchQuery || searchQuery.trim().length < 2) return []
    const q = searchQuery.toLowerCase()
    return allItems
      .filter((item) => {
        const content = (item.summary || item.content || '').toLowerCase()
        const tags = (item.tags || []).join(' ').toLowerCase()
        const agent = (item.agent_name || item.published_by_name || '').toLowerCase()
        const customer = (item.customer_name || '').toLowerCase()
        return content.includes(q) || tags.includes(q) || agent.includes(q) || customer.includes(q)
      })
      .sort((a, b) => (b.importance || 0) - (a.importance || 0))
      .slice(0, 20)
  }, [allItems, searchQuery])

  return (
    <div className="space-y-4">
      {/* Search input */}
      <div className="relative max-w-lg">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-ghost" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search episodic memories and knowledge base..."
          className={cn(
            'w-full pl-10 pr-4 py-2.5 rounded-xl text-sm',
            'bg-bg-subtle border border-border-subtle',
            'text-text-secondary placeholder:text-text-ghost',
            'focus:outline-none focus:border-accent/30',
            'transition-colors'
          )}
        />
      </div>

      {/* Results */}
      {searchQuery.trim().length < 2 ? (
        <div className="py-12 text-center">
          <p className="text-xs text-text-ghost">Type at least 2 characters to search</p>
        </div>
      ) : results.length === 0 ? (
        <div className="py-12 text-center">
          <p className="text-xs text-text-ghost">
            No results for &quot;{searchQuery}&quot;
          </p>
        </div>
      ) : (
        <div>
          <p className="text-xs text-text-muted mb-3">
            {results.length} result{results.length !== 1 ? 's' : ''} found
          </p>
          <div className="space-y-2">
            {results.map((item) => (
              <SearchResult key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
