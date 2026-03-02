import { useRef, useMemo, useState, useCallback, useEffect } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Html, Sparkles } from '@react-three/drei'
import * as THREE from 'three'

const LANE_COLORS = {
  control: '#6366F1',
  value: '#22C55E',
  support: '#EAB308',
  delivery: '#06B6D4',
}

const STATUS_COLORS = {
  active: '#6366F1',
  processing: '#818CF8',
  idle: '#27272A',
}

// Spherical coordinate positions for 10 agents by lane cluster
function getAgentPositions(count, radius) {
  const positions = []
  for (let i = 0; i < count; i++) {
    const phi = Math.acos(1 - (2 * (i + 1)) / (count + 1))
    const theta = Math.PI * (1 + Math.sqrt(5)) * i
    positions.push(
      new THREE.Vector3(
        radius * Math.sin(phi) * Math.cos(theta),
        radius * Math.cos(phi),
        radius * Math.sin(phi) * Math.sin(theta)
      )
    )
  }
  return positions
}

function AgentNode({ position, agent, isOrchestrator, onHover, onUnhover, onClick }) {
  const meshRef = useRef()
  const [hovered, setHovered] = useState(false)
  const isActive = agent.status === 'active' || agent.status === 'processing'
  const color = LANE_COLORS[agent.lane] || '#6366F1'
  const baseRadius = isOrchestrator ? 0.22 : 0.15

  useFrame((state) => {
    if (!meshRef.current) return
    const t = state.clock.elapsedTime

    // Pulse for orchestrator or active agents
    if (isOrchestrator || isActive) {
      const pulse = 1 + Math.sin(t * 2) * 0.1
      meshRef.current.scale.setScalar(hovered ? 1.3 : pulse)
    } else {
      meshRef.current.scale.setScalar(hovered ? 1.3 : 1)
    }
  })

  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        onPointerOver={(e) => {
          e.stopPropagation()
          setHovered(true)
          onHover?.(agent)
          document.body.style.cursor = 'pointer'
        }}
        onPointerOut={() => {
          setHovered(false)
          onUnhover?.()
          document.body.style.cursor = 'auto'
        }}
        onClick={(e) => {
          e.stopPropagation()
          onClick?.(agent.name)
        }}
      >
        <sphereGeometry args={[baseRadius, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={hovered ? 1.2 : isActive ? 0.5 : 0.2}
          transparent
          opacity={isActive ? 1 : 0.6}
        />
      </mesh>

      {/* Glow ring for active agents */}
      {isActive && (
        <pointLight color={color} distance={1.5} intensity={0.3} />
      )}

      {/* Sparkles for active */}
      {isActive && (
        <Sparkles count={5} size={1.5} scale={0.6} speed={0.3} color={color} />
      )}

      {/* Tooltip on hover */}
      {hovered && (
        <Html
          center
          distanceFactor={8}
          style={{ pointerEvents: 'none', whiteSpace: 'nowrap' }}
        >
          <div className="bg-bg-elevated px-3 py-1.5 rounded-lg border border-border"
            style={{ backdropFilter: 'blur(12px)' }}>
            <p className="font-mono text-xs text-text-primary font-semibold uppercase tracking-wider">
              {agent.display_name || agent.name?.replace(/_/g, ' ')}
            </p>
            <p className="font-mono text-xs mt-0.5"
              style={{ color: STATUS_COLORS[agent.status] || '#27272A' }}>
              {agent.status || 'idle'}
              {agent.tasks_today != null && ` · ${agent.tasks_today} tasks`}
            </p>
          </div>
        </Html>
      )}
    </group>
  )
}

function ConnectionLine({ start, end, isActive, color }) {
  const lineRef = useRef()
  const points = useMemo(() => [start, end], [start, end])
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry().setFromPoints(points)
    return geo
  }, [points])

  useFrame(() => {
    if (lineRef.current?.material) {
      lineRef.current.material.opacity = isActive ? 0.4 : 0.1
    }
  })

  return (
    <line ref={lineRef} geometry={geometry}>
      <lineDashedMaterial
        color={isActive ? color : '#6366F1'}
        opacity={isActive ? 0.4 : 0.1}
        transparent
        dashSize={isActive ? 0.15 : 0.1}
        gapSize={0.05}
        linewidth={1}
      />
    </line>
  )
}

function NeuralSphereScene({ agents, onAgentClick }) {
  const groupRef = useRef()
  const orchestratorPos = useMemo(() => new THREE.Vector3(0, 3, 0), [])

  const agentPositions = useMemo(() => {
    const nonOrch = agents.filter((a) => a.name !== 'cs_orchestrator')
    return getAgentPositions(nonOrch.length, 3)
  }, [agents])

  const orchAgent = useMemo(
    () => agents.find((a) => a.name === 'cs_orchestrator') || agents[0],
    [agents]
  )

  const nonOrchAgents = useMemo(
    () => agents.filter((a) => a.name !== 'cs_orchestrator'),
    [agents]
  )

  // Idle rotation
  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.02
    }
  })

  return (
    <group ref={groupRef}>
      {/* Wireframe icosahedron */}
      <mesh>
        <icosahedronGeometry args={[3, 2]} />
        <meshBasicMaterial
          wireframe
          color="#6366F1"
          transparent
          opacity={0.03}
        />
      </mesh>

      {/* Orchestrator node at top */}
      <AgentNode
        position={orchestratorPos}
        agent={orchAgent}
        isOrchestrator
        onClick={onAgentClick}
      />

      {/* Agent nodes */}
      {nonOrchAgents.map((agent, i) => {
        const pos = agentPositions[i]
        if (!pos) return null
        const isActive = agent.status === 'active' || agent.status === 'processing'
        const color = LANE_COLORS[agent.lane] || '#6366F1'

        return (
          <group key={agent.name}>
            <ConnectionLine
              start={orchestratorPos}
              end={pos}
              isActive={isActive}
              color={color}
            />
            <AgentNode
              position={pos}
              agent={agent}
              onClick={onAgentClick}
            />
          </group>
        )
      })}
    </group>
  )
}

export default function NeuralSphere({ agents = [], onAgentClick, onReady }) {
  useEffect(() => {
    onReady?.()
  }, [onReady])

  return (
    <div
      className="relative w-full"
      style={{ height: 340 }}
      aria-label="Neural Sphere — 10 AI agent nodes on rotating 3D globe"
    >
      <Canvas
        camera={{ position: [0, 2, 7], fov: 45 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.1} />
        <pointLight position={[0, 2, 7]} intensity={0.3} color="#6366F1" />
        <NeuralSphereScene agents={agents} onAgentClick={onAgentClick} />
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          dampingFactor={0.05}
          minPolarAngle={Math.PI * 0.2}
          maxPolarAngle={Math.PI * 0.8}
          autoRotate
          autoRotateSpeed={0.3}
        />
      </Canvas>
    </div>
  )
}
