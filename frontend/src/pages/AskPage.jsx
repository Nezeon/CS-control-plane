import { useEffect, useRef, useState } from 'react'
import { Send, Plus, Bot, User, Loader2, MessageCircle } from 'lucide-react'
import useChatStore from '../stores/chatStore'
import GlassCard from '../components/shared/GlassCard'
import LoadingSkeleton from '../components/shared/LoadingSkeleton'
import { formatRelativeTime } from '../utils/formatters'

export default function AskPage() {
  const {
    conversations, activeConversation, messages, isLoading, isSending,
    fetchConversations, loadConversation, sendMessage, newConversation,
  } = useChatStore()

  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => { fetchConversations() }, [fetchConversations])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isSending) return
    setInput('')
    sendMessage(text)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)] overflow-hidden">
      {/* Conversation list */}
      <div className="w-72 flex-shrink-0 border-r border-border-subtle flex flex-col bg-bg-subtle/50">
        <div className="p-3 border-b border-border-subtle">
          <button
            onClick={newConversation}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm rounded-lg bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
          >
            <Plus size={14} /> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {isLoading && conversations.length === 0 ? (
            <div className="p-3">
              <LoadingSkeleton variant="text" count={5} />
            </div>
          ) : conversations.length === 0 ? (
            <p className="p-4 text-xs text-text-ghost text-center">No conversations yet</p>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => loadConversation(conv.id)}
                className={`w-full text-left px-3 py-3 border-b border-border-subtle/50 hover:bg-bg-hover/50 transition-colors ${
                  activeConversation?.id === conv.id ? 'bg-bg-hover/70' : ''
                }`}
              >
                <p className="text-sm text-text-primary truncate">{conv.title || 'Untitled'}</p>
                <div className="flex items-center gap-2 mt-1">
                  {conv.customer_name && (
                    <span className="text-xxs text-text-muted truncate">{conv.customer_name}</span>
                  )}
                  <span className="text-xxs text-text-ghost font-mono">
                    {formatRelativeTime(conv.created_at || conv.updated_at)}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && !activeConversation ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <MessageCircle size={40} className="text-text-ghost mb-3" />
              <h2 className="text-lg font-display font-semibold text-text-primary mb-1">Ask anything</h2>
              <p className="text-sm text-text-muted max-w-md">
                Ask about customer health, tickets, agents, or any CS data. The AI orchestrator will route your query to the right specialist agent.
              </p>
              <div className="flex flex-wrap justify-center gap-2 mt-4">
                {[
                  'Which customer is at highest risk?',
                  'Show me open P1 tickets',
                  'Summarize recent call sentiment',
                  'What needs attention today?',
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); inputRef.current?.focus() }}
                    className="text-xs px-3 py-1.5 rounded-full bg-bg-active text-text-secondary hover:text-accent hover:bg-accent/10 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0 mt-1">
                      <Bot size={14} className="text-accent" />
                    </div>
                  )}
                  <div
                    className={`max-w-[70%] rounded-xl px-4 py-3 ${
                      msg.role === 'user'
                        ? 'bg-accent/15 text-text-primary'
                        : 'glass-mid text-text-secondary'
                    }`}
                  >
                    {msg.pipeline_status === 'processing' ? (
                      <div className="flex items-center gap-2 text-sm text-accent">
                        <Loader2 size={14} className="animate-spin" />
                        <span>Thinking...</span>
                      </div>
                    ) : (
                      <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                    )}
                    {msg.agents_involved?.length > 0 && msg.pipeline_status !== 'processing' && (
                      <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-border-subtle/50">
                        {msg.agents_involved.map((a) => (
                          <span key={a} className="text-xxs px-1.5 py-0.5 rounded bg-bg-active text-text-ghost font-mono">
                            {a}
                          </span>
                        ))}
                      </div>
                    )}
                    {msg.execution_metadata?.fast_path && (
                      <span className="text-xxs text-text-ghost mt-1 block">Fast path</span>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-7 h-7 rounded-full bg-bg-active flex items-center justify-center flex-shrink-0 mt-1">
                      <User size={14} className="text-text-muted" />
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-border-subtle p-4">
          <div className="flex items-end gap-3 max-w-3xl mx-auto">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about customers, tickets, health scores..."
              rows={1}
              className="flex-1 resize-none bg-bg-subtle border border-border rounded-xl px-4 py-3 text-sm text-text-primary placeholder:text-text-ghost focus:outline-none focus:border-accent min-h-[44px] max-h-32"
              style={{ height: 'auto', overflow: 'hidden' }}
              onInput={(e) => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px'
              }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isSending}
              className="flex-shrink-0 w-10 h-10 rounded-xl bg-accent text-white flex items-center justify-center hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {isSending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
