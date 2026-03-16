import { useRef, useMemo, useState, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Html, Sparkles } from '@react-three/drei'
import * as THREE from 'three'

const EMPTY_ARRAY = []

const TIER_COLORS = {
  1: '#7C5CFC', // Violet — Supervisor
  2: '#3B9EFF', // Blue — Lane Leads
  3: '#00E5C4', // Teal — Specialists
  4: '#5C5C72', // Slate — Foundation
}

const TIER_RADII = {
  1: 0,     // Center
  2: 2.0,   // Inner orbit
  3: 3.8,   // Middle orbit
  4: 5.0,   // Outer orbit
}

// Orbital speeds (radians per second) — different per tier for solar system feel
const TIER_ORBIT_SPEED = {
  2: 0.12,   // Slow
  3: 0.08,   // Medium
  4: -0.04,  // Slow reverse
}

const TIER_NODE_SIZE = {
  1: 0.38,
  2: 0.28,
  3: 0.22,
  4: 0.22,
}

function positionOnRing(radius, index, total) {
  if (total === 0) return new THREE.Vector3(0, 0, 0)
  const angle = (index / total) * Math.PI * 2 - Math.PI / 2
  return new THREE.Vector3(
    radius * Math.cos(angle),
    0,
    radius * Math.sin(angle)
  )
}

function AgentNode({ position, agent, onClick }) {
  const meshRef = useRef()
  const glowRef = useRef()
  const [hovered, setHovered] = useState(false)
  const isActive = agent.status === 'active' || agent.status === 'processing'
  const color = TIER_COLORS[agent.tier] || TIER_COLORS[3]
  const baseRadius = TIER_NODE_SIZE[agent.tier] || 0.22

  useFrame((state) => {
    if (!meshRef.current) return
    const t = state.clock.elapsedTime
    if (isActive) {
      const pulse = 1 + Math.sin(t * 2 + (agent.tier || 0)) * 0.15
      meshRef.current.scale.setScalar(hovered ? 1.4 : pulse)
    } else {
      meshRef.current.scale.setScalar(hovered ? 1.4 : 1)
    }
    // Animate glow ring
    if (glowRef.current) {
      glowRef.current.material.opacity = isActive
        ? 0.15 + Math.sin(t * 3) * 0.08
        : 0.05
    }
  })

  return (
    <group position={position}>
      {/* Outer glow ring */}
      <mesh ref={glowRef} rotation-x={-Math.PI / 2}>
        <ringGeometry args={[baseRadius * 1.3, baseRadius * 1.8, 32]} />
        <meshBasicMaterial color={color} transparent opacity={0.1} side={THREE.DoubleSide} />
      </mesh>

      {/* Main sphere */}
      <mesh
        ref={meshRef}
        onPointerOver={(e) => {
          e.stopPropagation()
          setHovered(true)
          document.body.style.cursor = 'pointer'
        }}
        onPointerOut={() => {
          setHovered(false)
          document.body.style.cursor = 'auto'
        }}
        onClick={(e) => {
          e.stopPropagation()
          onClick?.(agent.name || agent.agent_key)
        }}
      >
        <sphereGeometry args={[baseRadius, 24, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={hovered ? 1.6 : isActive ? 0.7 : 0.25}
          transparent
          opacity={isActive ? 1 : 0.7}
          roughness={0.2}
          metalness={0.3}
        />
      </mesh>

      {isActive && (
        <pointLight color={color} distance={2.5} intensity={0.5} />
      )}

      {isActive && (
        <Sparkles count={5} size={2} scale={1} speed={0.5} color={color} />
      )}

      {hovered && (
        <Html
          center
          distanceFactor={8}
          style={{ pointerEvents: 'none', whiteSpace: 'nowrap' }}
        >
          <div
            className="px-3 py-2 rounded-xl border border-white/10"
            style={{ backdropFilter: 'blur(16px)', background: 'rgba(12,13,16,0.9)' }}
          >
            <p className="font-display text-xs text-text-primary font-semibold">
              {agent.human_name || agent.display_name || agent.name}
            </p>
            <p className="text-[10px] text-text-muted mt-0.5">
              T{agent.tier} · {agent.role || agent.lane}
            </p>
            <p
              className="text-[10px] font-mono mt-0.5"
              style={{ color }}
            >
              {agent.status || 'idle'}
              {agent.tasks_today != null && ` · ${agent.tasks_today} tasks`}
            </p>
          </div>
        </Html>
      )}
    </group>
  )
}

// Visible orbit ring with glow
function OrbitRing({ radius, color }) {
  const ringRef = useRef()
  const glowRef = useRef()

  // Main ring points
  const geometry = useMemo(() => {
    const pts = []
    const segments = 128
    for (let i = 0; i <= segments; i++) {
      const angle = (i / segments) * Math.PI * 2
      pts.push(new THREE.Vector3(radius * Math.cos(angle), 0, radius * Math.sin(angle)))
    }
    return new THREE.BufferGeometry().setFromPoints(pts)
  }, [radius])

  // Dashed ring for sci-fi feel
  useEffect(() => {
    if (ringRef.current?.material) {
      ringRef.current.computeLineDistances()
    }
  }, [geometry])

  return (
    <group>
      {/* Solid subtle ring */}
      <line geometry={geometry}>
        <lineBasicMaterial color={color} transparent opacity={0.12} />
      </line>

      {/* Dashed brighter ring */}
      <line ref={ringRef} geometry={geometry}>
        <lineDashedMaterial
          color={color}
          transparent
          opacity={0.3}
          dashSize={0.3}
          gapSize={0.2}
          linewidth={1}
        />
      </line>

      {/* Flat ring mesh for glow effect */}
      <mesh ref={glowRef} rotation-x={-Math.PI / 2}>
        <ringGeometry args={[radius - 0.03, radius + 0.03, 128]} />
        <meshBasicMaterial color={color} transparent opacity={0.06} side={THREE.DoubleSide} />
      </mesh>
    </group>
  )
}

// Center sun glow for T1
function CenterSun({ color }) {
  const meshRef = useRef()

  useFrame((state) => {
    if (!meshRef.current) return
    const t = state.clock.elapsedTime
    meshRef.current.scale.setScalar(1 + Math.sin(t * 1.5) * 0.1)
    meshRef.current.material.opacity = 0.08 + Math.sin(t * 2) * 0.04
  })

  return (
    <group>
      {/* Inner glow sphere */}
      <mesh ref={meshRef}>
        <sphereGeometry args={[0.8, 32, 32]} />
        <meshBasicMaterial color={color} transparent opacity={0.1} />
      </mesh>
      {/* Core light */}
      <pointLight color={color} distance={6} intensity={0.8} />
    </group>
  )
}

function ConnectionLine({ start, end, colorEnd, isActive }) {
  const lineRef = useRef()
  const midY = useMemo(() => 0.3 + Math.random() * 0.3, [])

  const points = useMemo(() => {
    const mid = new THREE.Vector3(
      (start.x + end.x) / 2,
      midY,
      (start.z + end.z) / 2
    )
    const curve = new THREE.QuadraticBezierCurve3(start, mid, end)
    return curve.getPoints(20)
  }, [start, end, midY])

  const geometry = useMemo(() => new THREE.BufferGeometry().setFromPoints(points), [points])

  useFrame((state) => {
    if (!lineRef.current?.material) return
    if (isActive) {
      lineRef.current.material.opacity = 0.3 + Math.sin(state.clock.elapsedTime * 3) * 0.15
    } else {
      lineRef.current.material.opacity = 0.1
    }
  })

  return (
    <line ref={lineRef} geometry={geometry}>
      <lineBasicMaterial color={colorEnd} transparent opacity={0.1} />
    </line>
  )
}

// Tier orbit group — rotates all children at tier-specific speed
function TierOrbit({ tier, children }) {
  const groupRef = useRef()
  const speed = TIER_ORBIT_SPEED[tier] || 0

  useFrame((_, delta) => {
    if (groupRef.current && speed !== 0) {
      groupRef.current.rotation.y += delta * speed
    }
  })

  return <group ref={groupRef}>{children}</group>
}

function SolarSystemScene({ agents, onAgentClick }) {
  const { tierGroups, positions } = useMemo(() => {
    const groups = { 1: [], 2: [], 3: [], 4: [] }
    agents.forEach((a) => {
      const t = a.tier || 3
      if (groups[t]) groups[t].push(a)
    })

    const pos = new Map()
    Object.entries(groups).forEach(([tier, list]) => {
      const t = Number(tier)
      const radius = TIER_RADII[t]
      list.forEach((agent, i) => {
        const key = agent.id || agent.agent_key || agent.name
        const p = t === 1
          ? new THREE.Vector3(0, 0, 0)
          : positionOnRing(radius, i, list.length)
        pos.set(key, p)
      })
    })

    return { tierGroups: groups, positions: pos }
  }, [agents])

  // Build connections
  const connections = useMemo(() => {
    const conns = []
    const t1 = tierGroups[1]?.[0]
    const t1Key = t1 ? (t1.id || t1.agent_key || t1.name) : null
    const t1Pos = t1Key ? positions.get(t1Key) : null

    if (t1Pos) {
      tierGroups[2]?.forEach((a2) => {
        const k2 = a2.id || a2.agent_key || a2.name
        const p2 = positions.get(k2)
        if (p2) {
          const isActive = t1.status === 'active' || a2.status === 'active'
          conns.push({ start: t1Pos, end: p2, colorEnd: TIER_COLORS[2], isActive })
        }
      })
    }

    tierGroups[2]?.forEach((a2) => {
      const k2 = a2.id || a2.agent_key || a2.name
      const p2 = positions.get(k2)
      if (!p2) return
      const managed = a2.manages || []
      tierGroups[3]?.forEach((a3) => {
        const k3 = a3.agent_key || a3.name
        if (managed.includes(k3)) {
          const p3 = positions.get(a3.id || k3)
          if (p3) {
            const isActive = a2.status === 'active' || a3.status === 'active'
            conns.push({ start: p2, end: p3, colorEnd: TIER_COLORS[3], isActive })
          }
        }
      })
    })

    if (t1Pos) {
      tierGroups[4]?.forEach((a4) => {
        const k4 = a4.id || a4.agent_key || a4.name
        const p4 = positions.get(k4)
        if (p4) {
          conns.push({ start: t1Pos, end: p4, colorEnd: TIER_COLORS[4], isActive: false })
        }
      })
    }

    return conns
  }, [tierGroups, positions])

  return (
    <group>
      {/* Center sun glow */}
      <CenterSun color={TIER_COLORS[1]} />

      {/* Orbit rings — always visible */}
      {[2, 3, 4].map((t) => (
        <OrbitRing key={`orbit-${t}`} radius={TIER_RADII[t]} color={TIER_COLORS[t]} />
      ))}

      {/* Connection lines (static, don't orbit) */}
      {connections.map((c, i) => (
        <ConnectionLine key={`conn-${i}`} {...c} />
      ))}

      {/* T1 — Center, no orbit */}
      {tierGroups[1]?.map((agent) => {
        const key = agent.id || agent.agent_key || agent.name
        const pos = positions.get(key)
        if (!pos) return null
        return <AgentNode key={key} position={pos} agent={agent} onClick={onAgentClick} />
      })}

      {/* T2 — Inner orbit, slow rotation */}
      <TierOrbit tier={2}>
        {tierGroups[2]?.map((agent) => {
          const key = agent.id || agent.agent_key || agent.name
          const pos = positions.get(key)
          if (!pos) return null
          return <AgentNode key={key} position={pos} agent={agent} onClick={onAgentClick} />
        })}
      </TierOrbit>

      {/* T3 — Middle orbit, medium rotation */}
      <TierOrbit tier={3}>
        {tierGroups[3]?.map((agent) => {
          const key = agent.id || agent.agent_key || agent.name
          const pos = positions.get(key)
          if (!pos) return null
          return <AgentNode key={key} position={pos} agent={agent} onClick={onAgentClick} />
        })}
      </TierOrbit>

      {/* T4 — Outer orbit, slow reverse rotation */}
      <TierOrbit tier={4}>
        {tierGroups[4]?.map((agent) => {
          const key = agent.id || agent.agent_key || agent.name
          const pos = positions.get(key)
          if (!pos) return null
          return <AgentNode key={key} position={pos} agent={agent} onClick={onAgentClick} />
        })}
      </TierOrbit>
    </group>
  )
}

export default function NeuralSphere({ agents = EMPTY_ARRAY, onAgentClick, onReady }) {
  const glRef = useRef(null)

  useEffect(() => {
    onReady?.()
    return () => {
      if (glRef.current) {
        glRef.current.dispose()
        glRef.current = null
      }
    }
  }, [onReady])

  return (
    <div
      className="relative w-full h-full"
      style={{ minHeight: 420 }}
      aria-label="Solar System — 13 AI agents in 4-tier orbital hierarchy"
    >
      <Canvas
        camera={{ position: [0, 5, 7], fov: 50 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true, powerPreference: 'default' }}
        style={{ background: 'transparent' }}
        onCreated={({ gl }) => { glRef.current = gl }}
      >
        <ambientLight intensity={0.12} />
        <pointLight position={[0, 8, 5]} intensity={0.25} color="#7C5CFC" />
        <pointLight position={[-4, 3, -4]} intensity={0.15} color="#00E5C4" />
        <pointLight position={[4, 2, -3]} intensity={0.1} color="#3B9EFF" />
        <SolarSystemScene agents={agents} onAgentClick={onAgentClick} />
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          dampingFactor={0.05}
          minPolarAngle={Math.PI * 0.15}
          maxPolarAngle={Math.PI * 0.55}
          autoRotate
          autoRotateSpeed={0.15}
        />
      </Canvas>
    </div>
  )
}
