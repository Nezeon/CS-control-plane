import { useEffect, useState, useMemo } from 'react'
import { m } from 'framer-motion'
import { Clock, BookOpen, Search } from 'lucide-react'
import useMemoryStore from '../stores/memoryStore'
import TabBar from '../components/shared/TabBar'
import EpisodicTimeline from '../components/knowledge/EpisodicTimeline'
import KnowledgePool from '../components/knowledge/KnowledgePool'
import MemorySearch from '../components/knowledge/MemorySearch'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'

const tabs = [
  { key: 'episodic', label: 'Episodic Memory', icon: Clock },
  { key: 'knowledge', label: 'Knowledge Pool', icon: BookOpen },
  { key: 'search', label: 'Search', icon: Search },
]

export default function KnowledgePage() {
  const {
    episodicMemories,
    knowledgeEntries,
    searchResults,
    searchQuery,
    isLoading,
    fetchAll,
    setSelectedAgent,
    setSelectedLane,
    searchMemory,
    setSearchQuery,
  } = useMemoryStore()

  const [activeTab, setActiveTab] = useState('episodic')
  const [agentFilter, setAgentFilter] = useState('all')
  const [laneFilter, setLaneFilter] = useState('all')
  const [localSearchQuery, setLocalSearchQuery] = useState('')

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const handleAgentChange = (agent) => {
    setAgentFilter(agent)
    if (agent && agent !== 'all') {
      setSelectedAgent(agent)
    } else {
      // Fetch all episodic memories
      useMemoryStore.getState().fetchAllEpisodicMemories()
    }
  }

  const handleLaneChange = (lane) => {
    setLaneFilter(lane)
    setSelectedLane(lane === 'all' ? 'support' : lane)
  }

  const handleSearchChange = (query) => {
    setLocalSearchQuery(query)
    setSearchQuery(query)
    if (query.trim()) {
      searchMemory(query)
    }
  }

  // Combine episodic + knowledge for search fallback
  const allItems = useMemo(
    () => [
      ...episodicMemories.map((m) => ({ ...m, source: 'episodic' })),
      ...knowledgeEntries.map((k) => ({ ...k, source: 'semantic' })),
    ],
    [episodicMemories, knowledgeEntries]
  )

  if (isLoading && !episodicMemories.length && !knowledgeEntries.length) {
    return (
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-5">
        <div>
          <h1 className="text-xl font-display font-semibold text-text-primary mb-2">Knowledge</h1>
        </div>
        <LoadingSkeleton variant="card" count={4} />
      </div>
    )
  }

  return (
    <m.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-5"
    >
      {/* Header */}
      <div>
        <h1 className="text-xl font-display font-semibold text-text-primary mb-2">Knowledge</h1>
        <p className="text-xs text-text-muted">
          {episodicMemories.length} episodic memories &middot; {knowledgeEntries.length} knowledge entries
        </p>
      </div>

      {/* Tabs */}
      <TabBar tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} className="max-w-md" />

      {/* Tab content */}
      <div>
        {activeTab === 'episodic' && (
          <EpisodicTimeline
            memories={episodicMemories}
            selectedAgent={agentFilter}
            onAgentChange={handleAgentChange}
          />
        )}

        {activeTab === 'knowledge' && (
          <KnowledgePool
            entries={knowledgeEntries}
            selectedLane={laneFilter}
            onLaneChange={handleLaneChange}
          />
        )}

        {activeTab === 'search' && (
          <MemorySearch
            allItems={searchResults.length > 0 ? searchResults : allItems}
            searchQuery={localSearchQuery}
            onSearchChange={handleSearchChange}
          />
        )}
      </div>
    </m.div>
  )
}
