import { useEffect, useMemo, useState } from 'react'
import { m } from 'framer-motion'
import { MessageCircle, Bot, User, ChevronRight } from 'lucide-react'
import { cn } from '../utils/cn'
import { formatRelativeTime, formatTime } from '../utils/formatters'
import useMessageStore from '../stores/messageStore'
import useChatStore from '../stores/chatStore'
import ThreadList from '../components/conversations/ThreadList'
import ChatView from '../components/conversations/ChatView'
import EmptyChat from '../components/conversations/EmptyChat'
import GlassCard from '../components/shared/GlassCard'
import AgentAvatar from '../components/shared/AgentAvatar'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'

const AGENT_NAMES = {
  cso_orchestrator: 'Naveen Kapoor',
  support_lead: 'Rachel Torres',
  value_lead: 'Damon Reeves',
  delivery_lead: 'Priya Mehta',
  triage_agent: 'Kai Nakamura',
  troubleshooter: 'Leo Petrov',
  escalation_summary: 'Maya Santiago',
  health_monitor: 'Dr. Aisha Okafor',
  fathom_agent: 'Jordan Ellis',
  qbr_value: 'Sofia Marquez',
  sow_prerequisite: 'Ethan Brooks',
  deployment_intelligence: 'Zara Kim',
  customer_memory: 'Atlas',
}

const AGENT_TIERS = {
  cso_orchestrator: 1,
  support_lead: 2, value_lead: 2, delivery_lead: 2,
  triage_agent: 3, troubleshooter: 3, escalation_summary: 3,
  health_monitor: 3, fathom_agent: 3, qbr_value: 3,
  sow_prerequisite: 3, deployment_intelligence: 3,
  customer_memory: 4,
}

// ── User Chat Message Bubble ────────────────────────────────────────────
function UserChatMessage({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex gap-3', isUser ? 'flex-row-reverse' : 'flex-row')}>
      <div className="shrink-0 mt-1">
        {isUser ? (
          <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center border border-accent/30">
            <User className="w-3.5 h-3.5 text-accent" />
          </div>
        ) : (
          <div className="w-7 h-7 rounded-full bg-teal/10 flex items-center justify-center border border-teal/30">
            <Bot className="w-3.5 h-3.5 text-teal" />
          </div>
        )}
      </div>
      <div className={cn('flex-1 min-w-0', isUser ? 'max-w-[80%] ml-auto' : 'max-w-[85%]')}>
        <div className={cn('flex items-center gap-2 mb-1', isUser && 'justify-end')}>
          <span className="text-xs font-medium text-text-primary">{isUser ? 'You' : 'AI Assistant'}</span>
          <span className="text-xxs text-text-ghost font-mono">{formatTime(message.created_at)}</span>
        </div>
        <div className={cn(
          'rounded-2xl px-3 py-2.5 text-sm leading-relaxed',
          isUser
            ? 'bg-accent/10 border border-accent/20 text-text-primary'
            : 'border border-border-subtle text-text-secondary',
        )} style={!isUser ? { background: 'rgba(12, 13, 22, 0.6)' } : undefined}>
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        {/* Agents involved */}
        {!isUser && message.agents_involved?.length > 0 && (
          <div className="flex items-center gap-1 mt-1.5 flex-wrap">
            <span className="text-xxs text-text-ghost font-mono mr-1">Agents:</span>
            {message.agents_involved.map((agentId) => (
              <div key={agentId} className="flex items-center gap-0.5">
                <AgentAvatar name={AGENT_NAMES[agentId] || agentId} tier={AGENT_TIERS[agentId] || 3} size="sm" className="!w-4 !h-4 !text-[7px]" />
                <span className="text-xxs text-text-muted">{AGENT_NAMES[agentId] || agentId}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function ConversationsPage() {
  const [tab, setTab] = useState('agent')

  // Agent messages store
  const {
    threads,
    messages: agentMessages,
    selectedThread,
    selectedThreadMessages,
    filters,
    isLoading: agentLoading,
    fetchAll: fetchAgentMessages,
    selectThread,
    setFilter,
  } = useMessageStore()

  // User chats store
  const {
    conversations: chatConversations,
    messages: chatMessages,
    activeConversation: selectedChat,
    isLoading: chatLoading,
    fetchConversations,
    loadConversation,
  } = useChatStore()

  useEffect(() => {
    fetchAgentMessages()
  }, [fetchAgentMessages])

  useEffect(() => {
    if (tab === 'user_chat') fetchConversations()
  }, [tab, fetchConversations])

  const threadMessages = useMemo(
    () =>
      selectedThread && selectedThreadMessages.length > 0
        ? [...selectedThreadMessages].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
        : selectedThread
          ? agentMessages
              .filter((m) => m.thread_id === selectedThread.thread_id)
              .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
          : [],
    [selectedThread, selectedThreadMessages, agentMessages]
  )

  const isLoading = tab === 'agent' ? agentLoading : chatLoading

  if (isLoading && !threads.length && !chatConversations.length) {
    return (
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6">
        <h1 className="text-xl font-display font-semibold text-text-primary mb-5">Conversations</h1>
        <LoadingSkeleton variant="card" count={4} />
      </div>
    )
  }

  return (
    <m.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6"
    >
      {/* Header + Tabs */}
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-xl font-display font-semibold text-text-primary">Conversations</h1>
        <div className="flex gap-1.5">
          <button
            onClick={() => setTab('agent')}
            className={cn(
              'px-3 py-1.5 rounded-lg text-xs transition-colors',
              tab === 'agent'
                ? 'bg-accent/10 text-accent border border-accent/20'
                : 'text-text-muted hover:text-text-primary hover:bg-bg-hover',
            )}
          >
            Agent Messages
          </button>
          <button
            onClick={() => setTab('user_chat')}
            className={cn(
              'px-3 py-1.5 rounded-lg text-xs transition-colors',
              tab === 'user_chat'
                ? 'bg-accent/10 text-accent border border-accent/20'
                : 'text-text-muted hover:text-text-primary hover:bg-bg-hover',
            )}
          >
            User Chats
          </button>
        </div>
      </div>

      <div
        className="grid grid-cols-1 lg:grid-cols-5 gap-4"
        style={{ height: 'calc(100vh - 180px)' }}
      >
        {tab === 'agent' ? (
          <>
            {/* Agent Messages — Thread List */}
            <div className="lg:col-span-2 min-h-0">
              <ThreadList
                threads={threads}
                selectedThread={selectedThread}
                filter={filters.type}
                onFilterChange={(value) => setFilter('type', value)}
                onSelectThread={(thread) => selectThread(thread?.thread_id || thread)}
              />
            </div>
            {/* Agent Messages — Chat View */}
            <div className="lg:col-span-3 min-h-0">
              {selectedThread ? (
                <ChatView thread={selectedThread} messages={threadMessages} />
              ) : (
                <EmptyChat />
              )}
            </div>
          </>
        ) : (
          <>
            {/* User Chats — Conversation List */}
            <div className="lg:col-span-2 min-h-0">
              <GlassCard level="near" className="flex flex-col h-full p-0 overflow-hidden">
                <div className="px-4 py-3 border-b border-border-subtle">
                  <p className="text-xs font-medium text-text-muted uppercase tracking-wider">
                    Chat History
                  </p>
                </div>
                <div className="flex-1 overflow-y-auto">
                  {chatConversations.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 px-4">
                      <MessageCircle className="w-6 h-6 text-text-ghost mb-2" />
                      <p className="text-xs text-text-ghost text-center">
                        No user chats yet. Use Ask AI to start a conversation.
                      </p>
                    </div>
                  ) : (
                    chatConversations.map((conv) => (
                      <button
                        key={conv.id}
                        onClick={() => loadConversation(conv.id)}
                        className={cn(
                          'w-full text-left px-3 py-2.5 border-b border-border-subtle/50 transition-colors duration-100',
                          selectedChat?.id === conv.id
                            ? 'bg-accent-subtle border-l-2 border-l-accent'
                            : 'hover:bg-bg-hover border-l-2 border-l-transparent',
                        )}
                      >
                        <div className="flex items-center gap-2 mb-0.5">
                          <p className="text-sm text-text-primary truncate flex-1 font-medium">
                            {conv.title || 'New conversation'}
                          </p>
                          <ChevronRight className={cn('w-3 h-3 shrink-0', selectedChat?.id === conv.id ? 'text-accent' : 'text-text-ghost')} />
                        </div>
                        <div className="flex items-center gap-2">
                          {conv.customer_name && (
                            <span className="text-xxs text-teal font-mono truncate">{conv.customer_name}</span>
                          )}
                          <span className="text-xxs text-text-ghost ml-auto shrink-0">
                            {formatRelativeTime(conv.last_message_at || conv.created_at)}
                          </span>
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </GlassCard>
            </div>

            {/* User Chats — Message View */}
            <div className="lg:col-span-3 min-h-0">
              <GlassCard level="near" className="flex flex-col h-full p-0 overflow-hidden">
                {selectedChat ? (
                  <>
                    <div className="px-4 py-3 border-b border-border-subtle">
                      <h3 className="text-sm font-semibold text-text-primary truncate">
                        {selectedChat.title || 'Conversation'}
                      </h3>
                      {selectedChat.customer_name && (
                        <p className="text-xs text-teal font-mono">{selectedChat.customer_name}</p>
                      )}
                    </div>
                    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
                      {chatMessages.map((msg) => (
                        <UserChatMessage key={msg.id} message={msg} />
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full">
                    <MessageCircle className="w-8 h-8 text-text-ghost/40 mb-3" />
                    <p className="text-sm text-text-muted">Select a conversation to view</p>
                  </div>
                )}
              </GlassCard>
            </div>
          </>
        )}
      </div>
    </m.div>
  )
}
