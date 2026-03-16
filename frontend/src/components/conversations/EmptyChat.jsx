import { MessageSquare } from 'lucide-react'
import GlassCard from '../shared/GlassCard'

export default function EmptyChat() {
  return (
    <GlassCard level="mid" className="flex flex-col items-center justify-center h-full">
      <div className="w-14 h-14 rounded-2xl bg-bg-active flex items-center justify-center mb-4">
        <MessageSquare className="w-6 h-6 text-text-ghost" />
      </div>
      <p className="text-sm font-medium text-text-muted mb-1">Select a conversation</p>
      <p className="text-xs text-text-ghost">
        Choose a thread from the list to view agent communication
      </p>
    </GlassCard>
  )
}
