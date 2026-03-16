import { useState } from 'react'
import { m, AnimatePresence } from 'framer-motion'
import GlassCard from './GlassCard'

export default function EmailDraftCard({ draft, participants = [], subject = '', onClose }) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedDraft, setEditedDraft] = useState(draft || '')
  const [copied, setCopied] = useState(false)

  const toLine = participants
    .map((p) => `${p.name} <${p.email}>`)
    .join(', ')

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(editedDraft)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback
      const ta = document.createElement('textarea')
      ta.value = editedDraft
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (!draft) return null

  return (
    <m.div
      initial={{ opacity: 0, y: 20, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.97 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
    >
      <GlassCard level="near" className="relative overflow-hidden">
        {/* Draft badge */}
        <div className="absolute top-3 right-3 flex items-center gap-2">
          <span className="px-2 py-0.5 text-[10px] font-bold tracking-widest uppercase rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
            Draft -- Not Sent
          </span>
          {onClose && (
            <button
              onClick={onClose}
              className="w-6 h-6 flex items-center justify-center rounded-full bg-white/5 hover:bg-white/10 text-white/40 hover:text-white/80 transition-colors text-xs"
            >
              x
            </button>
          )}
        </div>

        {/* Header */}
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-white/90 font-display mb-3">
            Generated Email Draft
          </h3>

          {/* Email metadata */}
          <div className="space-y-1.5 text-xs font-mono">
            {toLine && (
              <div className="flex gap-2">
                <span className="text-white/40 w-14 shrink-0">To:</span>
                <span className="text-cyan-300/80 break-all">{toLine}</span>
              </div>
            )}
            {subject && (
              <div className="flex gap-2">
                <span className="text-white/40 w-14 shrink-0">Subject:</span>
                <span className="text-white/70">{subject}</span>
              </div>
            )}
          </div>
        </div>

        {/* Divider */}
        <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent mb-4" />

        {/* Email body */}
        <AnimatePresence mode="wait">
          {isEditing ? (
            <m.textarea
              key="editor"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              value={editedDraft}
              onChange={(e) => setEditedDraft(e.target.value)}
              className="w-full min-h-[300px] bg-white/5 border border-white/10 rounded-lg p-3 text-sm text-white/80 font-mono leading-relaxed resize-y focus:outline-none focus:border-teal-500/50 focus:ring-1 focus:ring-teal-500/20"
              autoFocus
            />
          ) : (
            <m.div
              key="preview"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="whitespace-pre-wrap text-sm text-white/70 leading-relaxed font-mono bg-white/[0.02] rounded-lg p-3 border border-white/5 max-h-[400px] overflow-y-auto"
            >
              {editedDraft}
            </m.div>
          )}
        </AnimatePresence>

        {/* Actions */}
        <div className="flex items-center gap-2 mt-4">
          <button
            onClick={handleCopy}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              copied
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-teal-500/10 text-teal-400 border border-teal-500/20 hover:bg-teal-500/20'
            }`}
          >
            {copied ? 'Copied!' : 'Copy to Clipboard'}
          </button>

          <button
            onClick={() => setIsEditing(!isEditing)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              isEditing
                ? 'bg-violet-500/20 text-violet-400 border border-violet-500/30'
                : 'bg-white/5 text-white/60 border border-white/10 hover:bg-white/10'
            }`}
          >
            {isEditing ? 'Preview' : 'Edit Draft'}
          </button>
        </div>
      </GlassCard>
    </m.div>
  )
}
