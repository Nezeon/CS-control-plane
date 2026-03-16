import { lazy, Suspense, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import useDashboardStore from '../../stores/dashboardStore'
import useSettingsStore from '../../stores/settingsStore'
import StatusIndicator from '../shared/StatusIndicator'
import AgentAvatar from '../shared/AgentAvatar'
import LoadingSkeleton from '../shared/LoadingSkeleton'

const NeuralSphere = lazy(() => import('../../three/NeuralSphere'))

const LANE_COLORS = {
  control: 'border-l-accent',
  value: 'border-l-status-success',
  support: 'border-l-status-warning',
  delivery: 'border-l-data',
}

function Agent2DGrid({ agents, navigate }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 flex-1">
      {agents.map((agent) => {
        const laneColor = LANE_COLORS[agent.lane] || 'border-l-border'
        return (
          <button
            key={agent.id || agent.name}
            onClick={() => navigate('/agents')}
            className={`text-left px-3 py-2.5 rounded-lg bg-bg-active/40 border border-border-subtle ${laneColor} border-l-2 hover:bg-bg-active/70 transition-colors`}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <AgentAvatar
                name={agent.human_name || agent.display_name || agent.name}
                tier={agent.tier || 3}
                size="sm"
                status={agent.status}
                className="w-5 h-5 text-[9px]"
              />
              <span className="text-xs font-medium text-text-primary truncate">
                {(agent.human_name || agent.display_name || agent.name || '')
                  .replace('CS ', '')
                  .replace(' Agent', '')}
              </span>
            </div>
            <p className="text-xxs text-text-ghost font-mono tabular-nums">
              {agent.tasks_today || 0} tasks
            </p>
          </button>
        )
      })}
    </div>
  )
}

export default function NeuralSphereWrapper() {
  const agents = useDashboardStore((s) => s.agents)
  const navigate = useNavigate()
  const reducedMotion = useSettingsStore?.((s) => s.reducedMotion) ?? false

  const { activeCount, idleCount, totalTasks } = useMemo(() => {
    if (!agents?.length) return { activeCount: 0, idleCount: 0, totalTasks: 0 }
    return {
      activeCount: agents.filter((a) => a.status === 'active' || a.status === 'processing').length,
      idleCount: agents.filter((a) => a.status === 'idle').length,
      totalTasks: agents.reduce((sum, a) => sum + (a.tasks_today || 0), 0),
    }
  }, [agents])

  if (!agents?.length) {
    return (
      <div className="card p-4">
        <LoadingSkeleton variant="rect" width="100%" height={360} />
      </div>
    )
  }

  return (
    <div className="card p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-medium text-text-primary">Agent Status</h2>
        <button
          onClick={() => navigate('/agents')}
          className="text-xxs text-text-ghost hover:text-accent transition-colors"
        >
          View all →
        </button>
      </div>

      {/* 3D scene with 2D fallback */}
      <div className="flex-1 min-h-0">
        {reducedMotion ? (
          <Agent2DGrid agents={agents} navigate={navigate} />
        ) : (
          <Suspense fallback={<Agent2DGrid agents={agents} navigate={navigate} />}>
            <NeuralSphere
              agents={agents}
              onAgentClick={() => navigate('/agents')}
            />
          </Suspense>
        )}
      </div>

      {/* Footer stats */}
      <div className="flex items-center gap-4 mt-3 pt-3 border-t border-border-subtle">
        <span className="text-xxs text-text-ghost">
          <span className="text-status-success font-medium">{activeCount}</span> active
        </span>
        <span className="text-xxs text-text-ghost">
          <span className="text-text-muted font-medium">{idleCount}</span> idle
        </span>
        <span className="text-xxs text-text-ghost ml-auto font-mono tabular-nums">
          {totalTasks} tasks today
        </span>
      </div>
    </div>
  )
}
