import { useState } from 'react'
import { m, AnimatePresence } from 'framer-motion'
import api from '../../services/api'
import EmailDraftCard from '../shared/EmailDraftCard'

const SCENARIOS = [
  {
    id: 'ticket',
    label: 'Ticket Triage',
    desc: 'P1 scanner failure -- full triage pipeline',
    agents: 'Naveen -> Rachel -> Kai',
    color: 'cyan',
  },
  {
    id: 'meeting',
    label: 'Meeting Followup',
    desc: 'Q1 review call -- summary + email draft',
    agents: 'Naveen -> Damon -> Riley',
    color: 'violet',
  },
  {
    id: 'all',
    label: 'Full Demo',
    desc: 'Both scenarios sequentially',
    agents: 'All agents',
    color: 'teal',
  },
]

function findDraftEmail(obj, depth = 0) {
  if (depth > 8 || !obj || typeof obj !== 'object') return null
  if (obj.draft_email) return obj
  for (const val of Object.values(obj)) {
    const found = findDraftEmail(val, depth + 1)
    if (found) return found
  }
  return null
}

export default function DemoTrigger() {
  const [isOpen, setIsOpen] = useState(false)
  const [running, setRunning] = useState(null) // scenario id
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [emailDraft, setEmailDraft] = useState(null)

  const handleRun = async (scenarioId) => {
    setRunning(scenarioId)
    setResult(null)
    setError(null)
    setEmailDraft(null)

    try {
      const { data } = await api.post('/demo/trigger', { scenario: scenarioId }, { timeout: 120000 })
      setResult(data)

      // Extract email draft from meeting result
      if (data.results?.meeting?.result) {
        const draftData = findDraftEmail(data.results.meeting.result)
        if (draftData) {
          setEmailDraft({
            draft: draftData.draft_email,
            participants: data.results.meeting.result?.orchestrator_result?.output?.deliverables?.value?.output?.specialist_outputs?.meeting_followup?.output?.participants || [],
            subject: `Follow-up: ${data.results.meeting.result?.orchestrator_result?.output?.deliverables?.value?.output?.specialist_outputs?.meeting_followup?.output?.summary || 'Meeting Notes'}`,
          })
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setRunning(null)
    }
  }

  return (
    <>
      {/* Floating trigger button */}
      <m.button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-full bg-gradient-to-r from-teal-500/90 to-violet-500/90 text-white text-sm font-semibold shadow-lg shadow-teal-500/20 hover:shadow-teal-500/40 transition-shadow"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
        Run Demo
      </m.button>

      {/* Panel */}
      <AnimatePresence>
        {isOpen && (
          <m.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-20 right-6 z-50 w-80 glass-near rounded-xl overflow-hidden shadow-2xl shadow-black/50"
          >
            {/* Header */}
            <div className="px-4 py-3 border-b border-white/10">
              <h3 className="text-sm font-semibold text-white/90 font-display">
                Demo Scenarios
              </h3>
              <p className="text-[11px] text-white/40 mt-0.5">
                Watch agents work in real-time
              </p>
            </div>

            {/* Scenario buttons */}
            <div className="p-3 space-y-2">
              {SCENARIOS.map((s) => (
                <button
                  key={s.id}
                  onClick={() => handleRun(s.id)}
                  disabled={running !== null}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                    running === s.id
                      ? 'border-teal-500/50 bg-teal-500/10'
                      : 'border-white/5 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/10'
                  } ${running && running !== s.id ? 'opacity-40' : ''}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-white/90">{s.label}</span>
                    {running === s.id && (
                      <span className="flex items-center gap-1 text-[10px] text-teal-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                        Running...
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-white/40 mt-0.5">{s.desc}</p>
                  <p className="text-[10px] text-white/25 mt-0.5 font-mono">{s.agents}</p>
                </button>
              ))}
            </div>

            {/* Status */}
            {error && (
              <div className="px-3 pb-3">
                <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-[11px] text-rose-400">
                  {error}
                </div>
              </div>
            )}

            {result && (
              <div className="px-3 pb-3">
                <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-400">
                  Demo complete! Check terminal for pipeline logs.
                  {Object.entries(result.results || {}).map(([k, v]) => (
                    <div key={k} className="mt-1 text-white/50">
                      {k}: {v.elapsed_ms}ms
                    </div>
                  ))}
                </div>
              </div>
            )}
          </m.div>
        )}
      </AnimatePresence>

      {/* Email Draft Modal */}
      <AnimatePresence>
        {emailDraft && (
          <m.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm"
            onClick={() => setEmailDraft(null)}
          >
            <m.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="w-full max-w-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <EmailDraftCard
                draft={emailDraft.draft}
                participants={emailDraft.participants}
                subject={emailDraft.subject}
                onClose={() => setEmailDraft(null)}
              />
            </m.div>
          </m.div>
        )}
      </AnimatePresence>
    </>
  )
}
