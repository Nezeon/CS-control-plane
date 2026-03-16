import { useState } from 'react'
import { AnimatePresence, m } from 'framer-motion'
import { ChevronRight, CheckCircle2, XCircle, Loader, Clock, Wrench } from 'lucide-react'
import { cn } from '../../utils/cn'

const statusConfig = {
  completed: { icon: CheckCircle2, color: 'text-teal', bg: 'bg-teal-subtle' },
  running: { icon: Loader, color: 'text-accent', bg: 'bg-accent-subtle' },
  failed: { icon: XCircle, color: 'text-status-danger', bg: 'bg-red-500/10' },
  pending: { icon: Clock, color: 'text-text-ghost', bg: 'bg-bg-active' },
}

const stageLabels = {
  perceive: 'Perceive',
  retrieve: 'Retrieve',
  think: 'Think',
  act: 'Act',
  reflect: 'Reflect',
  quality_gate: 'Quality Gate',
  finalize: 'Finalize',
}

function formatObj(obj) {
  if (!obj) return null
  if (typeof obj === 'string') return obj
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

function StageRow({ round, index }) {
  const [expanded, setExpanded] = useState(false)
  const config = statusConfig[round.status] || statusConfig.pending
  const StatusIcon = config.icon

  // Support both data formats
  const stageName = round.stage_type || round.stage || 'unknown'
  const stageDisplayName = round.stage_name || stageLabels[stageName] || stageName
  const inputData = round.input_summary || round.input
  const outputData = round.output_summary || round.output
  const tokensUsed = round.tokens_used || 0

  return (
    <div className="border-b border-border-subtle last:border-0">
      {/* Stage header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-bg-hover/50 transition-colors text-left"
      >
        <ChevronRight
          className={cn(
            'w-3.5 h-3.5 text-text-ghost transition-transform shrink-0',
            expanded && 'rotate-90'
          )}
        />
        <span className="text-xxs text-text-ghost font-mono w-5">{index + 1}</span>
        <div className={cn('w-6 h-6 rounded-md flex items-center justify-center shrink-0', config.bg)}>
          <StatusIcon className={cn('w-3.5 h-3.5', config.color, round.status === 'running' && 'animate-spin')} />
        </div>
        <span className="text-sm font-medium text-text-primary w-28 shrink-0">
          {stageDisplayName}
        </span>
        <span className="text-xs text-text-muted flex-1 truncate">
          {typeof outputData === 'string'
            ? outputData
            : outputData
              ? Object.values(outputData).join(', ').slice(0, 80)
              : (typeof inputData === 'string' ? inputData : '—')}
        </span>
        {round.duration_ms != null && (
          <span className="text-xxs font-mono text-text-ghost shrink-0">
            {round.duration_ms >= 1000
              ? `${(round.duration_ms / 1000).toFixed(1)}s`
              : `${round.duration_ms}ms`}
          </span>
        )}
        {tokensUsed > 0 && (
          <span className="text-xxs font-mono text-text-ghost shrink-0 w-16 text-right">
            {tokensUsed} tok
          </span>
        )}
      </button>

      {/* Expanded detail */}
      <AnimatePresence>
        {expanded && (
          <m.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pl-16 space-y-3">
              {/* Input */}
              {inputData && (
                <div>
                  <p className="text-xxs font-mono text-text-ghost uppercase tracking-wider mb-1">Input</p>
                  <div className="rounded-lg bg-bg-subtle border border-border-subtle p-2.5">
                    <pre className="text-xs text-text-secondary font-mono leading-relaxed whitespace-pre-wrap break-all">
                      {formatObj(inputData)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Output */}
              {outputData && (
                <div>
                  <p className="text-xxs font-mono text-text-ghost uppercase tracking-wider mb-1">Output</p>
                  <div className="rounded-lg bg-bg-subtle border border-border-subtle p-2.5">
                    <pre className="text-xs text-text-secondary font-mono leading-relaxed whitespace-pre-wrap break-all">
                      {formatObj(outputData)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Confidence */}
              {round.confidence != null && (
                <div className="flex items-center gap-2">
                  <span className="text-xxs font-mono text-text-ghost">Confidence:</span>
                  <span className="text-xs font-mono text-teal">{Math.round(round.confidence * 100)}%</span>
                </div>
              )}

              {/* Tools called */}
              {round.tools_called && round.tools_called.length > 0 && (
                <div>
                  <p className="text-xxs font-mono text-text-ghost uppercase tracking-wider mb-1">
                    Tools ({round.tools_called.length})
                  </p>
                  <div className="space-y-1.5">
                    {round.tools_called.map((tool, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-2 rounded-lg bg-bg-subtle border border-border-subtle px-3 py-2"
                      >
                        <Wrench className="w-3 h-3 text-accent shrink-0" />
                        <span className="text-xs font-mono text-accent">{tool.name || tool.tool_name}</span>
                        {tool.duration_ms != null && (
                          <span className="text-xxs font-mono text-text-ghost">
                            {tool.duration_ms}ms
                          </span>
                        )}
                        {(tool.args || tool.arguments) && (
                          <span className="text-xxs text-text-ghost truncate flex-1 text-right">
                            {Object.entries(tool.args || tool.arguments)
                              .map(([k, v]) => `${k}=${typeof v === 'string' ? `"${v}"` : v}`)
                              .join(', ')}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </m.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function PipelineTrace({ rounds }) {
  if (!rounds || rounds.length === 0) {
    return (
      <div className="px-4 py-6 text-center">
        <p className="text-xs text-text-ghost">No execution data available</p>
      </div>
    )
  }

  return (
    <div className="border-t border-border-subtle bg-bg-subtle/30 rounded-b-xl">
      {rounds.map((round, i) => (
        <StageRow key={round.round_id || i} round={round} index={i} />
      ))}
    </div>
  )
}
