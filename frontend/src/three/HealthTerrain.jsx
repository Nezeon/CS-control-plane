import { useRef, useMemo, useState, useCallback } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Html } from '@react-three/drei'
import * as THREE from 'three'

const GRID_W = 64
const GRID_H = 48
const PLANE_W = 8
const PLANE_H = 6

function healthToColor(score) {
  // Green peaks → amber mid → red valleys
  if (score >= 75) {
    const t = (score - 75) / 25
    return new THREE.Color('#EAB308').lerp(new THREE.Color('#22C55E'), t)
  } else if (score >= 40) {
    const t = (score - 40) / 35
    return new THREE.Color('#EF4444').lerp(new THREE.Color('#EAB308'), t)
  } else {
    const t = score / 40
    return new THREE.Color('#7F1D1D').lerp(new THREE.Color('#EF4444'), t)
  }
}

function buildTerrainGeometry(customers) {
  const geometry = new THREE.PlaneGeometry(PLANE_W, PLANE_H, GRID_W, GRID_H)
  const positions = geometry.attributes.position
  const colors = new Float32Array(positions.count * 3)
  const vertexScores = new Float32Array(positions.count)

  // Place customers as "peaks" on the terrain
  const customerPositions = customers.map((c, i) => {
    // Distribute customers across the grid
    const col = i % Math.ceil(Math.sqrt(customers.length))
    const row = Math.floor(i / Math.ceil(Math.sqrt(customers.length)))
    const cols = Math.ceil(Math.sqrt(customers.length))
    const rows = Math.ceil(customers.length / cols)
    return {
      x: ((col + 0.5) / cols - 0.5) * PLANE_W,
      z: ((row + 0.5) / rows - 0.5) * PLANE_H,
      score: c.health_score || 50,
      customer: c,
    }
  })

  for (let i = 0; i < positions.count; i++) {
    const vx = positions.getX(i)
    const vy = positions.getY(i)

    // Calculate height based on proximity to customers
    let totalInfluence = 0
    let weightedScore = 0
    const radius = 2.0

    for (const cp of customerPositions) {
      const dx = vx - cp.x
      const dy = vy - cp.z
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < radius) {
        const influence = Math.pow(1 - dist / radius, 2)
        totalInfluence += influence
        weightedScore += cp.score * influence
      }
    }

    const score = totalInfluence > 0 ? weightedScore / totalInfluence : 30
    const height = (score / 100) * 1.2

    positions.setZ(i, height)
    vertexScores[i] = score

    const color = healthToColor(score)
    colors[i * 3] = color.r
    colors[i * 3 + 1] = color.g
    colors[i * 3 + 2] = color.b
  }

  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  geometry.computeVertexNormals()

  return { geometry, customerPositions }
}

function TerrainMesh({ customers, onHoverCustomer }) {
  const meshRef = useRef()
  const wireRef = useRef()
  const { raycaster, pointer, camera } = useThree()
  const [hoveredIdx, setHoveredIdx] = useState(-1)

  const { geometry, customerPositions } = useMemo(
    () => buildTerrainGeometry(customers),
    [customers]
  )

  // Subtle undulation
  const basePositions = useMemo(() => {
    const pos = geometry.attributes.position
    return Float32Array.from(pos.array)
  }, [geometry])

  useFrame((state) => {
    if (!meshRef.current) return
    const t = state.clock.elapsedTime
    const positions = meshRef.current.geometry.attributes.position

    for (let i = 0; i < positions.count; i++) {
      const baseZ = basePositions[i * 3 + 2]
      const x = basePositions[i * 3]
      const y = basePositions[i * 3 + 1]
      const wave = Math.sin(x * 0.5 + t * 0.4) * Math.cos(y * 0.5 + t * 0.3) * 0.03
      positions.setZ(i, baseZ + wave)
    }
    positions.needsUpdate = true

    // Copy to wireframe
    if (wireRef.current) {
      wireRef.current.geometry.attributes.position.array.set(
        meshRef.current.geometry.attributes.position.array
      )
      wireRef.current.geometry.attributes.position.needsUpdate = true
    }
  })

  const handlePointerMove = useCallback(
    (e) => {
      e.stopPropagation()
      const point = e.point
      let closest = -1
      let minDist = 0.8

      for (let i = 0; i < customerPositions.length; i++) {
        const cp = customerPositions[i]
        const dx = point.x - cp.x
        const dy = point.y - cp.z
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < minDist) {
          minDist = dist
          closest = i
        }
      }

      if (closest !== hoveredIdx) {
        setHoveredIdx(closest)
        onHoverCustomer?.(closest >= 0 ? customerPositions[closest].customer : null)
        document.body.style.cursor = closest >= 0 ? 'pointer' : 'auto'
      }
    },
    [customerPositions, hoveredIdx, onHoverCustomer]
  )

  const handlePointerLeave = useCallback(() => {
    setHoveredIdx(-1)
    onHoverCustomer?.(null)
    document.body.style.cursor = 'auto'
  }, [onHoverCustomer])

  return (
    <group rotation={[-Math.PI / 2, 0, 0]}>
      {/* Solid terrain with vertex colors */}
      <mesh
        ref={meshRef}
        geometry={geometry}
        onPointerMove={handlePointerMove}
        onPointerLeave={handlePointerLeave}
      >
        <meshStandardMaterial
          vertexColors
          transparent
          opacity={0.85}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Wireframe overlay */}
      <mesh ref={wireRef} geometry={geometry.clone()}>
        <meshBasicMaterial
          wireframe
          color="#6366F1"
          transparent
          opacity={0.03}
        />
      </mesh>

      {/* Customer markers */}
      {customerPositions.map((cp, i) => {
        const isHovered = i === hoveredIdx
        const color = healthToColor(cp.score)
        const height = (cp.score / 100) * 1.2

        return (
          <group key={cp.customer.id || i} position={[cp.x, cp.z, height + 0.1]}>
            {/* Marker dot */}
            <mesh>
              <sphereGeometry args={[isHovered ? 0.12 : 0.08, 8, 8]} />
              <meshBasicMaterial color={color} />
            </mesh>

            {/* Glow for high-risk */}
            {cp.score < 50 && (
              <pointLight color="#EF4444" distance={1} intensity={0.2} />
            )}

            {/* Tooltip on hover */}
            {isHovered && (
              <Html
                center
                distanceFactor={8}
                position={[0, 0, 0.3]}
                style={{ pointerEvents: 'none', whiteSpace: 'nowrap' }}
              >
                <div className="bg-bg-elevated px-3 py-1.5 rounded-lg border border-border"
                  style={{ backdropFilter: 'blur(12px)' }}>
                  <p className="font-mono text-xs text-text-primary font-semibold uppercase tracking-wider">
                    {cp.customer.company_name || cp.customer.name || 'Unknown'}
                  </p>
                  <p className="font-mono text-xs mt-0.5" style={{ color: `#${color.getHexString()}` }}>
                    Health: {Math.round(cp.score)}
                    {cp.customer.risk_level && ` · ${cp.customer.risk_level.replace(/_/g, ' ')}`}
                  </p>
                </div>
              </Html>
            )}
          </group>
        )
      })}
    </group>
  )
}

export default function HealthTerrain({ customers = [], onCustomerClick }) {
  return (
    <group>
      <TerrainMesh customers={customers} onHoverCustomer={() => {}} />
      <OrbitControls
        enableZoom={false}
        enablePan={false}
        dampingFactor={0.05}
        minPolarAngle={Math.PI * 0.1}
        maxPolarAngle={Math.PI * 0.45}
        autoRotate
        autoRotateSpeed={0.15}
      />
    </group>
  )
}
