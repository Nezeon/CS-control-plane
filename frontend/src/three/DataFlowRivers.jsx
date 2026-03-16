import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { Html } from '@react-three/drei'
import * as THREE from 'three'

const STREAMS = [
  { label: 'JIRA', dest: 'TRIAGE', color: '#7C5CFC', yOffset: 1.2 },
  { label: 'FATHOM', dest: 'CALL INT', color: '#3B9EFF', yOffset: 0 },
  { label: 'CRON', dest: 'HEALTH', color: '#00E5A0', yOffset: -1.2 },
]

const PARTICLES_PER_STREAM = 50
const TOTAL_PARTICLES = STREAMS.length * PARTICLES_PER_STREAM

function buildCurve(yOffset) {
  return new THREE.CubicBezierCurve3(
    new THREE.Vector3(-4, yOffset, 0),
    new THREE.Vector3(-1.2, yOffset * 0.3, 0),
    new THREE.Vector3(1.2, yOffset * 0.3, 0),
    new THREE.Vector3(4, yOffset, 0)
  )
}

function CurveLines({ streams }) {
  return streams.map((s, i) => {
    const curve = buildCurve(s.yOffset)
    const points = curve.getPoints(48)
    const geometry = new THREE.BufferGeometry().setFromPoints(points)
    return (
      <line key={`stream-${i}`} geometry={geometry}>
        <lineBasicMaterial color={s.color} transparent opacity={0.08} />
      </line>
    )
  })
}

function ParticleSystem() {
  const meshRef = useRef()
  const dummy = useMemo(() => new THREE.Object3D(), [])

  const curves = useMemo(
    () => STREAMS.map((s) => buildCurve(s.yOffset)),
    []
  )

  const colors = useMemo(() => {
    const arr = new Float32Array(TOTAL_PARTICLES * 3)
    for (let si = 0; si < STREAMS.length; si++) {
      const c = new THREE.Color(STREAMS[si].color)
      for (let pi = 0; pi < PARTICLES_PER_STREAM; pi++) {
        const idx = (si * PARTICLES_PER_STREAM + pi) * 3
        arr[idx] = c.r
        arr[idx + 1] = c.g
        arr[idx + 2] = c.b
      }
    }
    return arr
  }, [])

  // Each particle has t (0→1), speed, and phase offset
  const particleData = useMemo(() => {
    const data = []
    for (let si = 0; si < STREAMS.length; si++) {
      for (let pi = 0; pi < PARTICLES_PER_STREAM; pi++) {
        data.push({
          stream: si,
          t: Math.random(),
          speed: 0.3 + Math.random() * 0.5,
        })
      }
    }
    return data
  }, [])

  useFrame((_, delta) => {
    if (!meshRef.current) return

    for (let i = 0; i < TOTAL_PARTICLES; i++) {
      const p = particleData[i]
      p.t += delta * p.speed * 0.15
      if (p.t > 1) p.t -= 1

      const curve = curves[p.stream]
      const pos = curve.getPointAt(p.t)

      // Slight lateral jitter
      pos.y += Math.sin(p.t * Math.PI * 4 + i) * 0.03
      pos.z += Math.cos(p.t * Math.PI * 3 + i * 0.7) * 0.02

      dummy.position.copy(pos)
      const scale = 0.6 + Math.sin(p.t * Math.PI) * 0.4
      dummy.scale.setScalar(scale)
      dummy.updateMatrix()
      meshRef.current.setMatrixAt(i, dummy.matrix)
    }
    meshRef.current.instanceMatrix.needsUpdate = true
  })

  return (
    <instancedMesh ref={meshRef} args={[null, null, TOTAL_PARTICLES]}>
      <sphereGeometry args={[0.03, 6, 6]} />
      <meshBasicMaterial transparent opacity={0.8} />
      <instancedBufferAttribute
        attach="instanceColor"
        args={[colors, 3]}
      />
    </instancedMesh>
  )
}

function CenterDiamond() {
  const ref = useRef()

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.3
      ref.current.rotation.z = Math.PI / 4
    }
  })

  return (
    <mesh ref={ref} position={[0, 0, 0]}>
      <octahedronGeometry args={[0.2, 0]} />
      <meshBasicMaterial
        color="#7C5CFC"
        wireframe
        transparent
        opacity={0.4}
      />
    </mesh>
  )
}

export default function DataFlowRivers() {
  const streams = STREAMS

  return (
    <group>
      {/* Static curve paths */}
      <CurveLines streams={streams} />

      {/* Instanced particle system */}
      <ParticleSystem />

      {/* Center diamond */}
      <CenterDiamond />

      {/* Source labels (left) */}
      {streams.map((s, i) => (
        <Html
          key={`src-${i}`}
          position={[-4.8, s.yOffset, 0]}
          center
          distanceFactor={10}
          style={{ pointerEvents: 'none', whiteSpace: 'nowrap' }}
        >
          <span
            className="font-mono text-xs uppercase tracking-wider font-medium"
            style={{ color: s.color, opacity: 0.7 }}
          >
            {s.label}
          </span>
        </Html>
      ))}

      {/* Destination labels (right) */}
      {streams.map((s, i) => (
        <Html
          key={`dest-${i}`}
          position={[4.8, s.yOffset, 0]}
          center
          distanceFactor={10}
          style={{ pointerEvents: 'none', whiteSpace: 'nowrap' }}
        >
          <span className="font-mono text-xs uppercase tracking-wider text-text-muted">
            {s.dest}
          </span>
        </Html>
      ))}
    </group>
  )
}
