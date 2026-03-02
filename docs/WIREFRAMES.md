# HivePro CS Control Plane — Premium Visual Specification

**Design Tier:** Award-winning enterprise spatial dashboard  
**Author:** Ayushmaan Singh Naruka  
**Version:** 2.0 (Premium Redesign)  
**Date:** February 27, 2026

---

## 1. Design System — "Deep Ocean Bioluminescence"

### 1.1 Design Philosophy

This is NOT a traditional dashboard. It is a **spatial command center** — a living 3D environment where data exists in physical space. Five principles govern every design decision:

1. **Spatial Depth** — Three visual layers: Background (void), Midground (content), Foreground (overlays). Parallax on mouse movement.
2. **Living Data** — Nothing is static. Numbers breathe, connections pulse, agents orbit. The dashboard feels alive even idle.
3. **Cinematic Transitions** — Moving between sections feels like a camera moving through 3D space, not page switches.
4. **Information Hierarchy Through Depth** — Critical data floats closer to the viewer. Less important data recedes.
5. **Zero Chrome** — No visible borders, no traditional buttons. Interactions discovered through light, glow, and spatial cues.

---

### 1.2 Color Palette — Bioluminescent

Inspired by deep ocean bioluminescent creatures — colors that glow from within against absolute darkness. Two-tone accent system (teal + violet) instead of mono-teal.

```
VOID LAYER (Background)
  --void-black:         #020408         Absolute deep space (body bg)
  --void-gradient-1:    #030810         Upper void
  --void-gradient-2:    #040610         Lower void
  --nebula-blue:        rgba(8, 24, 58, 0.4)    Subtle nebula clouds

ATMOSPHERE (Ambient light — large radial gradients that shift slowly)
  --atmo-teal:          rgba(0, 245, 212, 0.03)  Ambient teal fog
  --atmo-violet:        rgba(139, 92, 246, 0.03) Ambient violet mist
  --atmo-cyan:          rgba(34, 211, 238, 0.02) Ambient cyan haze

BIOLUMINESCENT ACCENTS (Primary palette — self-glowing)
  --bio-teal:           #00F5D4          Primary accent (electric teal)
  --bio-violet:         #8B5CF6          Secondary accent (rich violet)
  --bio-cyan:           #22D3EE          Tertiary accent (ice cyan)
  --bio-magenta:        #F472B6          Alert/escalation accent
  --bio-amber:          #FBBF24          Warning accent (golden amber)
  --bio-emerald:        #34D399          Success/healthy accent
  --bio-rose:           #FB7185          Danger/critical accent

GLOW INTENSITIES (per color — 3 levels)
  --glow-subtle:        0 0 20px rgba(0, 245, 212, 0.08)
  --glow-medium:        0 0 40px rgba(0, 245, 212, 0.15)
  --glow-intense:       0 0 60px rgba(0, 245, 212, 0.25), 0 0 120px rgba(0, 245, 212, 0.08)
  /* Replace teal RGB with any accent color for that color's glow */

SURFACES — "Frosted Depth" (NOT glassmorphism — more ethereal)
  --surface-1:          rgba(8, 16, 32, 0.65)     Near panel (closest to user)
  --surface-2:          rgba(8, 16, 32, 0.45)     Mid panel
  --surface-3:          rgba(8, 16, 32, 0.25)     Far panel (most transparent)
  --surface-border:     rgba(0, 245, 212, 0.06)   Whisper border (barely visible)
  --surface-glow:       rgba(0, 245, 212, 0.12)   Hover border (glows on interaction)
  --surface-blur:       20px                        Backdrop blur amount

SEVERITY MAPPING
  --severity-p1:        #FB7185          P1 Critical (rose)
  --severity-p2:        #FBBF24          P2 High (amber)
  --severity-p3:        #22D3EE          P3 Medium (cyan)
  --severity-p4:        #64748B          P4 Low (slate)

AGENT LANE COLORS
  --lane-control:       #00F5D4          Orchestrator + Memory (teal)
  --lane-value:         #34D399          Health, Call Intel, QBR (emerald)
  --lane-support:       #FBBF24          Ticket Triage, Troubleshoot, Escalation (amber)
  --lane-delivery:      #22D3EE          SOW, Deployment Intel (cyan)

TEXT
  --text-bright:        #F1F5F9          Headlines, critical numbers
  --text-primary:       #CBD5E1          Body text
  --text-muted:         #64748B          Labels, metadata
  --text-ghost:         #334155          Disabled, background labels
  --text-accent:        #00F5D4          Highlighted/linked text
  --text-violet:        #8B5CF6          Secondary highlights
```

**Animated Background Mesh:**
```css
body {
  background:
    radial-gradient(ellipse at 20% 50%, rgba(0, 245, 212, 0.04) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(139, 92, 246, 0.04) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(34, 211, 238, 0.03) 0%, transparent 50%),
    #020408;
  /* Gradient positions shift slowly over 30s — breathing nebula effect */
}
```

---

### 1.3 Typography — "Precision Meets Humanity"

Contrast between cold precision (display/data) and warm readability (body).

```
DISPLAY — Hero numbers, page titles, section headers
  Font:     'Space Grotesk', sans-serif
  Weights:  500, 600, 700
  Style:    Uppercase, letter-spacing 3-8px
  Import:   https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700

DATA — Agent names, labels, IDs, timestamps, badges, monospace data
  Font:     'IBM Plex Mono', monospace
  Weights:  400, 500, 600
  Style:    Uppercase for labels, normal for values
  Import:   https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600

BODY — Descriptions, summaries, paragraphs, tooltips
  Font:     'Inter', sans-serif
  Weights:  400, 500, 600
  Style:    Normal case, optimized line-height
  Import:   https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600

TYPE SCALE
  --text-xs:    0.6875rem / 11px    (micro labels, badge text)
  --text-sm:    0.8125rem / 13px    (secondary labels, timestamps)
  --text-base:  0.9375rem / 15px    (body text)
  --text-lg:    1.125rem / 18px     (card titles, descriptions)
  --text-xl:    1.375rem / 22px     (section headers)
  --text-2xl:   1.75rem / 28px      (page titles)
  --text-3xl:   2.25rem / 36px      (large stat numbers)
  --text-4xl:   3rem / 48px         (hero KPI numbers)
  --text-5xl:   4rem / 64px         (hero health score)

USAGE MAP
  Page titles:       Space Grotesk 600, text-2xl, uppercase, letter-spacing 4px, --text-bright
  Section headers:   Space Grotesk 500, text-xl, uppercase, letter-spacing 2px, --text-bright
  KPI hero numbers:  Space Grotesk 700, text-4xl/5xl, --text-bright
  Card titles:       Inter 600, text-lg, --text-primary
  Body text:         Inter 400, text-base, --text-primary, line-height 1.7
  Labels:            IBM Plex Mono 500, text-xs, uppercase, letter-spacing 1.5px, --text-muted
  Data values:       IBM Plex Mono 400, text-sm, --text-primary
  Agent names:       IBM Plex Mono 600, text-sm, uppercase, letter-spacing 1px
  Timestamps:        IBM Plex Mono 400, text-xs, --text-ghost
  Badges:            IBM Plex Mono 500, text-xs, uppercase
  Breadcrumbs:       Inter 500, text-sm, --text-muted (active: --text-accent)
```

---

### 1.4 Surface / Card System — "Frosted Depth"

Three depth levels. Cards don't have hard borders — they emerge from the void through subtle light differences.

```css
/* Level 1 — Nearest to user. Primary panels, active cards. */
.surface-near {
  background: rgba(8, 16, 32, 0.65);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 245, 212, 0.06);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.03);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.surface-near:hover {
  border-color: rgba(0, 245, 212, 0.12);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4), 0 0 30px rgba(0, 245, 212, 0.06);
  transform: translateY(-2px);
}

/* Level 2 — Midground. Secondary panels, stats containers. */
.surface-mid {
  background: rgba(8, 16, 32, 0.45);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

/* Level 3 — Background. Ambient panels, decoration. */
.surface-far {
  background: rgba(8, 16, 32, 0.25);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.02);
  border-radius: 8px;
}

/* Interactive Card — 3D tilt on hover (rotateX/Y based on mouse position, max 3deg) */
.surface-interactive {
  /* inherits surface-near */
  cursor: pointer;
  transform-style: preserve-3d;
  perspective: 1000px;
}
.surface-interactive:hover {
  /* JS applies rotateX/rotateY based on cursor position within the card */
  /* max rotation: 3 degrees */
  box-shadow: 0 16px 64px rgba(0, 0, 0, 0.5), 0 0 40px rgba(0, 245, 212, 0.08);
}
```

---

### 1.5 3D Elements (React Three Fiber / Three.js)

#### 3D-1: NEURAL SPHERE (Command Center hero)

A slowly rotating 3D sphere/globe made of interconnected nodes and edges. The 10 AI agents are plotted as glowing nodes ON the sphere surface.

**Implementation:** React Three Fiber (`@react-three/fiber` + `@react-three/drei`)

**Geometry:**
- Sphere wireframe: IcosahedronGeometry(radius=3, detail=2), wireframe material, --bio-teal at 4% opacity
- Agent nodes: SphereGeometry(radius=0.15) with emissive material, color = lane color
- Connection lines: BufferGeometry lines connecting Orchestrator to each agent, dashed
- Orchestrator node: at top ("north pole"), 1.5x size of other nodes

**Behavior:**
- Idle: sphere rotates at 0.1 deg/sec on Y-axis
- Mouse drag: rotate freely with OrbitControls (dampingFactor=0.05)
- Hover node: node scales to 1.3x, emissive intensity increases, tooltip appears (HTML overlay via drei Html component), connected lines glow brighter
- Click node: camera animates (smooth tween via gsap or drei) to zoom into node, then transitions to Agent Detail view
- Active agent: node pulsing aura (animated emissive), emits tiny particles (drei Sparkles)
- Data flow: when event routes, a glowing particle (small sphere) travels along the connection line from Orchestrator to target agent (animated position along curve)

**Lighting:**
- Ambient light: intensity 0.1
- Point light at camera position: intensity 0.3, --bio-teal color
- Each active node: PointLight with small range, node's lane color

**Performance:** InstancedMesh for nodes, max 30 connection particles at once, requestAnimationFrame throttled to 60fps.

#### 3D-2: HEALTH TERRAIN MAP (Command Center bottom-left)

Customer health as a 3D topographic terrain. Healthy = tall peaks. At-risk = deep valleys.

**Implementation:** Three.js PlaneGeometry with vertex displacement

**Geometry:**
- PlaneGeometry(width=8, height=6, widthSegments=64, heightSegments=48)
- Vertex Y positions displaced based on customer health score positions (Gaussian blobs at each customer's grid position)
- ShaderMaterial with gradient: emerald (peaks) → amber (mid) → rose (valleys)

**Behavior:**
- Default: bird's-eye camera (looking down at ~60deg angle)
- Mouse wheel: zoom (clamped min/max)
- Drag: pan
- Hover over peak/valley: raycasting → tooltip with customer name + score + risk level
- Click: camera flies down to customer location → transitions to Customer Detail
- Idle: terrain has subtle wave undulation (sine wave vertex animation, very slow)
- Grid lines: wireframe overlay at ~3% opacity

#### 3D-3: FLOATING METRIC ORBS (Command Center, 4 positions)

KPI stats as floating 3D holographic spheres.

**Implementation:** Three.js SphereGeometry with custom shader material

**Geometry:**
- SphereGeometry(radius=0.8, segments=32)
- Custom shader: iridescent/holographic effect (fresnel-based color shift)
- Inner glow: emissive with bloom post-processing

**Behavior:**
- Float with sine-wave bobbing (different phase per orb): `y = baseY + sin(time * 0.5 + phase) * 0.1`
- Parallax on mouse movement: orbs shift position based on cursor (transform: translate based on mouse offset)
- Number rendered as HTML overlay (drei Html) centered on orb
- Trend arrow orbits the orb on a small elliptical path
- Hover: orb brightens, slight scale-up to 1.1x

#### 3D-4: DATA FLOW RIVERS (Command Center, horizontal band)

Events as particle streams flowing through the interface.

**Implementation:** Three.js Points/InstancedMesh with animated positions

**Geometry:**
- 3 horizontal bezier curves (one per source: Jira, Fathom, Cron)
- Each curve has N particles (InstancedMesh spheres, radius=0.02)
- Particles travel along curve at varying speeds

**Behavior:**
- Particles continuously flow left → right, recycling at edges
- Particle color: teal (ticket), violet (call), cyan (health), amber (alert)
- Curves converge at center (Orchestrator node) then branch to destination agents
- New event: burst of brighter/larger particles at source, propagates through
- Hover stream: particles slow, tooltip shows recent events
- Click particle: shows specific event detail

#### 3D-5: TICKET CONSTELLATION (Ticket Warroom, default view)

Tickets as stars in 3D space.

**Implementation:** React Three Fiber, InstancedMesh for stars

**Mapping:**
- X-axis: severity (P1=left, P4=right)
- Y-axis: age (new=bottom, old=top)
- Z-axis: status (open=front, resolved=back)

**Behavior:**
- Stars connected by faint lines if same customer
- Star size: P1=largest (radius 0.1), P4=smallest (radius 0.03)
- Star color: rose (open), amber (in-progress), cyan (waiting), emerald (resolved)
- Hover: star scales 2x, shows summary tooltip
- Click: camera focuses → side drawer opens with ticket detail
- SLA breaching: red pulsing ring (drei Ring with animated opacity)
- OrbitControls for free rotation/zoom

**Fallback:** Toggle to premium 2D table view (see Page 6).

---

### 1.6 Background Effects

#### Nebula Mesh (replaces flat grid)
```css
/* Animated gradient mesh — positions shift over 30 seconds */
.nebula-bg {
  position: fixed;
  inset: 0;
  background:
    radial-gradient(ellipse at var(--nebula-x1, 20%) var(--nebula-y1, 50%), rgba(0, 245, 212, 0.04) 0%, transparent 50%),
    radial-gradient(ellipse at var(--nebula-x2, 80%) var(--nebula-y2, 20%), rgba(139, 92, 246, 0.04) 0%, transparent 50%),
    radial-gradient(ellipse at var(--nebula-x3, 50%) var(--nebula-y3, 80%), rgba(34, 211, 238, 0.03) 0%, transparent 50%);
  animation: nebulaShift 30s ease-in-out infinite alternate;
  pointer-events: none;
  z-index: 0;
}
/* JS animates --nebula-x/y CSS variables for smooth gradient movement */
```

#### Particle Field (replaces floating particles)
- Canvas-based, 50 particles max
- Particles: 1-2px radius, mixed colors (teal 60%, violet 25%, cyan 15%)
- Opacity: 0.05-0.15 (very subtle)
- Behavior: slow drift upward + slight horizontal oscillation + very slow parallax on mouse
- Performance: requestAnimationFrame, no interaction detection

#### Depth Vignette
```css
.depth-vignette {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at center, transparent 40%, rgba(2, 4, 8, 0.6) 100%);
  pointer-events: none;
  z-index: 1;
}
```

---

### 1.7 Component Library

#### Status Indicator (replaces badges — use glowing dots + label)
- Shape: 8px circle with glow halo
- Colors map: active=--bio-teal, idle=--text-ghost, healthy=--bio-emerald, watch=--bio-amber, high_risk=--bio-rose, processing=--bio-violet
- Active: pulsing animation (scale 1→1.8→1, opacity 1→0.4→1, 2s loop)
- Label: IBM Plex Mono 500, text-xs, uppercase, same color as dot but dimmer

#### Health Ring (3D on detail pages, 2D elsewhere)
- **2D version (cards/lists):** SVG circular arc, stroke-dasharray animated
  - Track: rgba(255,255,255,0.04)
  - Progress: gradient stroke from --bio-emerald (100) through --bio-amber (50) to --bio-rose (0)
  - Center: score in Space Grotesk 700
  - Sizes: sm=40px, md=64px, lg=96px
  - Mount animation: stroke-dashoffset animates in 1.5s ease-out
- **3D version (customer detail hero):** Three.js TorusGeometry
  - Slowly rotating (0.2 deg/sec)
  - Emissive material with health color
  - Score as drei Html overlay at center
  - Particle sparkles at the progress endpoint

#### Animated Counter
- Number scrambles through random digits before settling on final value (slot machine effect)
- Duration: 1.5s for scramble + 0.5s settle
- Font: Space Grotesk 700
- Easing: ease-out-expo

#### Metric Orb (2D fallback for smaller contexts)
- Circle with radial gradient (center bright, edges fade)
- Inner glow effect via box-shadow
- Number centered, label below
- Subtle float animation (translateY oscillation)

#### Event Pulse Item
- Layout: [glowing dot] [timestamp] [description] [customer pill]
- Dot: 6px, color by event type, with glow
- Timestamp: IBM Plex Mono 400, text-xs, --text-ghost
- Description: Inter 400, text-sm, --text-primary
- Customer: frosted pill badge (surface-far style)
- Entry: slides in + fades from 0 to 1, 400ms ease-out
- Click: ripple emanation from dot

#### Severity Marker
- NOT a colored pill. A colored LIGHT — small rectangle with matching glow
- P1: rose bar + rose glow, P2: amber bar + amber glow, P3: cyan bar, P4: slate bar (no glow)
- Width: 3px, height: full card height (left edge ribbon)

#### Sentiment Wave (mini)
- Tiny SVG waveform (40px × 16px) per insight card
- Shape: randomized smooth curve, amplitude based on sentiment intensity
- Color: emerald (positive) → slate (neutral) → rose (negative)
- Animates drawing left-to-right on mount

#### Command Palette (Cmd+K)
- Center-screen modal, 600px width, surface-near card
- Search input at top: large, no border, just bottom divider line
- Results below: categorized (Pages, Customers, Tickets, Agents, Actions)
- Each result: icon + text + category badge
- Keyboard navigation: arrow keys, Enter to select
- Fuzzy search (fuse.js)
- Opens with fade+scale from 0.95 to 1

---

## 2. Navigation — Orbital Menu

### 2.1 Primary Navigation (Orbital Arc)

**Replaces sidebar entirely.** A curved arc of navigation icons at the bottom-center of the viewport, like a gaming HUD.

```
Layout (bottom-center, fixed position):

                    ╭──╮   ╭──╮   ╭────╮   ╭──╮   ╭──╮
                    │⚙️│   │👥│   │ ◆  │   │🎙️│   │🎫│
                    ╰──╯   ╰──╯   ╰────╯   ╰──╯   ╰──╯
                                   ACTIVE
              ◁ Settings                        Reports ▷
```

**Implementation:**
- Fixed to bottom-center of viewport, 80px height
- 7 items on a CSS perspective arc (transform: rotateY per item based on position)
- Items (left to right): Settings, Customers, Agents, **Dashboard** (center default), Insights, Tickets, Reports
- Frosted glass backing strip (surface-mid, wide pill shape)

**Item States:**
- **Active (center):** 1.5x scale, full --bio-teal glow, label visible below, icon bright
- **Adjacent (±1):** 1x scale, dimmer icon, label hidden (appears on hover)
- **Far (±2, ±3):** 0.85x scale, very dim, smaller

**Transitions:**
- Click non-active item: arc rotates smoothly (500ms cubic-bezier), clicked item moves to center
- Content area transitions with a 3D camera movement feel (scale + opacity)
- Active item has a small upward-pointing light beam/indicator beneath it

**Parallax:** Entire arc shifts very slightly (±5px) based on mouse horizontal position.

### 2.2 Command Palette (Cmd+K / Ctrl+K)

Always available global search. Power-user navigation.

**Categories:**
- 🏠 Pages — Dashboard, Customers, Agents, etc.
- 👤 Customers — Search by name
- 🎫 Tickets — Search by Jira ID or summary
- 🤖 Agents — Jump to agent detail
- ⚡ Actions — Run Health Check, Sync Fathom, Generate Report

### 2.3 Breadcrumb Trail (top-left, floating)

When drilling into details (Dashboard → Customers → Acme Corp → JIRA-1234):
- Floating breadcrumb at top-left, above content
- Each crumb: Inter 500, text-sm
- Separator: animated dot (●) with short connecting line
- Active crumb: --text-accent
- Past crumbs: --text-muted (clickable)
- Click past crumb: animate "camera zoom out" transition to that level

### 2.4 Top Bar (minimal, floating)

NOT a full-width bar. Floating elements at top of viewport.
- Top-left: Breadcrumb trail
- Top-right cluster: [Cmd+K search icon] [Notification bell + count badge] [User avatar dropdown]
- No background — items float on the void
- Items have subtle surface-far backing on hover

---

## 3. Page Layouts

### 3.1 Command Center (Dashboard) — Full Immersive Viewport

No sidebar. No traditional grid. Content fills the entire viewport with 3D elements.

```
┌──────────────────────────────────────────────────────────────────┐
│ [Breadcrumb: Mission Control]                  [⌘K]  [🔔3]  [👤] │
│                                                                  │
│         ╭─────╮                          ╭─────╮                │
│         │ 47  │                          │  5  │                │
│         │CUST │    ┌──────────────┐      │RISK │                │
│         │ +3↑ │    │              │      │ +2↑ │                │
│         ╰─────╯    │   NEURAL    │      ╰─────╯                │
│                     │   SPHERE   │                              │
│    ╭─────╮         │             │         ╭─────╮             │
│    │ 23  │         │  (3D Globe  │         │ 71% │             │
│    │TKTS │         │   rotating  │         │HLTH │             │
│    │ -4↓ │         │   with 10   │         │ +5↑ │             │
│    ╰─────╯         │   agent     │         ╰─────╯             │
│                     │   nodes)   │                              │
│                     │             │                              │
│                     │  ~500px ⌀  │                              │
│                     └──────────────┘                              │
│                                                                  │
│  ═══════════════ DATA FLOW RIVERS ════════════════════           │
│  Jira  ~~●●~~●~>  ◆ ORCHESTRATOR  ~~●●~>  Triage  ~~●~>  ✓    │
│  Fathom ~●~~●●~>  ◆ ORCHESTRATOR  ~~●~>  CallInt  ~●~>  ✓    │
│  Cron  ~~~●~~●~>  ◆ ORCHESTRATOR  ~~●●~>  Health  ~~●●~>  ⚠   │
│                                                                  │
│  ┌───────────────────────────┐  ┌────────────────────────────┐  │
│  │                           │  │                            │  │
│  │    HEALTH TERRAIN         │  │    LIVE PULSE              │  │
│  │    (3D Topographic Map)   │  │    (EKG-style timeline)    │  │
│  │                           │  │                            │  │
│  │    ▲ Delta(91) ▲ Eta(85)  │  │  ─╱╲──╱╲╲╱──╱╲───        │  │
│  │   ▲ Beta(78)  ▲ Theta(72)│  │                            │  │
│  │      ▽ Gamma(55)         │  │  14:23 ● Ticket triaged    │  │
│  │   ▽ Acme(42) ▽ Iota(44) │  │  14:22 ● Health updated    │  │
│  │     ▽ Epsilon(38)        │  │  14:21 ● Call processed    │  │
│  │                           │  │  14:20 ● ALERT fired      │  │
│  │  [Rotatable, zoomable]    │  │  14:19 ● Report done      │  │
│  └───────────────────────────┘  └────────────────────────────┘  │
│                                                                  │
│          ╭──╮  ╭──╮  ╭────╮  ╭──╮  ╭──╮                       │
│          │⚙│  │👥│  │ ◆◆ │  │🎙│  │🎫│     ORBITAL NAV       │
│          ╰──╯  ╰──╯  ╰────╯  ╰──╯  ╰──╯                       │
└──────────────────────────────────────────────────────────────────┘
```

**Section: Floating Metric Orbs (4 positions around Neural Sphere)**
- Positioned at NW, NE, SW, SE relative to the sphere
- Each orb: 3D holographic sphere (or 2D fallback: radial gradient circle)
- Content: Number (Space Grotesk 700, text-4xl) + Label (IBM Plex Mono 500, text-xs) + Trend pill
- Float animation: each orb bobs on a different sine phase
- Parallax: shift ±15px based on cursor position

**Section: Neural Sphere (Center, ~40% of viewport height)**
- THE hero. The showpiece.
- See 3D-1 specification above
- Canvas element: `<Canvas>` from @react-three/fiber
- Overlaid with HTML labels for agent names via drei `<Html>`

**Section: Data Flow Rivers (Below sphere, ~80px band)**
- 3 horizontal particle streams
- Source icons on left edge (Jira icon, Fathom icon, Cron icon) — static, labeled
- Particles flow → center (Orchestrator diamond) → branch to agent icons on right
- See 3D-4 specification above
- If no 3D: CSS-only version with animated dots on SVG paths

**Section: Health Terrain (Bottom-left, ~50% width)**
- surface-near card, 280px height
- Header: "HEALTH TERRAIN" (Space Grotesk 500, text-xs, uppercase, --text-muted)
- Contains Three.js canvas (see 3D-2 spec)
- Footer: "Click to explore" hint text

**Section: Live Pulse (Bottom-right, ~50% width)**
- surface-near card, 280px height
- Header: "LIVE PULSE" with animated green dot
- Top half: EKG/heartbeat-style waveform (Canvas 2D or SVG)
  - Each event = a pulse on the line
  - Pulse height = severity (P1 tallest)
  - Pulse color = event type
  - Continuously scrolls right-to-left
- Bottom half: Latest 5-6 event text entries (scrollable)
- Each entry: [dot] [HH:MM] [description] [customer pill]

---

### 3.2 Customer Observatory

Three view modes: Solar System (3D default), Premium Grid (2D), Data Table.

**Solar System View (Default):**
- Full section (same card area as the Terrain/Pulse section on dashboard), ~60% viewport height
- Customers as planets orbiting center point
- Inner orbit: Enterprise (largest planets)
- Middle orbit: Mid-Market
- Outer orbit: SMB (smallest)
- Planet color: health gradient (emerald → amber → rose)
- Planet size: relative to tier importance
- Health score label near each planet
- Planets orbit slowly (different speeds per orbit)
- Interactive: hover = enlarge + tooltip, click = fly-in to Customer Detail

**Quick Intel Panel (below the main view):**
- surface-near card, 120px height, appears when any customer is hovered/selected
- Left: Customer name (Space Grotesk 600, text-xl) + industry/tier pills
- Center: 4 mini stat blocks (Health, Tickets, Calls, Alerts) — each with number + trend
- Right: Latest event text + "DEEP DIVE →" button (--bio-teal, glow on hover)

**Premium Grid View (Toggle):**
- Cards in responsive grid (4 cols desktop, 3 tablet, 2 mobile, 1 small mobile)
- Each card: surface-interactive
  - 3D tilt on hover (max 3deg rotateX/Y)
  - Top: Customer name (Inter 600, text-lg)
  - Center: Health Ring (md, 64px) with score
  - Bottom row: Industry pill + Tier pill + Risk count + Renewal countdown
  - Left edge: severity ribbon (3px, color by risk level)
  - Cards sorted by risk (worst first). At-risk cards have subtle rose glow at edges.

**Data Table View (Toggle):**
- surface-near card with premium table
- Columns: Name, Health (mini ring), Industry, Tier, Risk Level, Open Tickets, CS Owner, Renewal, Last Call
- Sortable headers (click = sort, indicator arrow)
- Row hover: row lifts slightly (translateY -1px) + surface-glow border
- Left severity ribbon on each row
- Click row → Customer Detail

**View Toggle:** 3 icons in filter bar — Solar System icon / Grid icon / Table icon. Active = --bio-teal fill.

**Filter Bar (above the view):**
- Search input (surface-mid, search icon, "Search customers...")
- Dropdown pills: Risk Level, CS Owner, Sort By — each as a surface-far pill that opens a dropdown on click
- View toggle (right side)

---

### 3.3 Customer Deep Dive — Vertical Scroll Journey

Full-screen immersive view. The page is a vertical scroll journey — each section reveals with scroll-triggered animations like a premium annual report.

**SECTION 1: HERO (Viewport height)**
- Customer name: Space Grotesk 700, text-5xl (64px), uppercase, letter-spacing 8px, centered
- Subtitle: "Enterprise · Banking · Since Jun 2025" — Inter 400, text-lg, --text-muted, centered
- 3D Health Ring: centered, 200px diameter (Three.js torus, slowly rotating)
- Score inside ring: Space Grotesk 700, text-5xl
- Risk level badge below ring: large pill with glow
- Bottom row: 3 info blocks (Renewal Countdown | CS Owner | Primary Contact) — surface-mid cards, centered row
- Scroll hint at very bottom: animated chevron pointing down

**SECTION 2: HEALTH STORY (Scroll-reveal)**
- Header: "HEALTH TRAJECTORY" — Space Grotesk 500, text-xl
- Area chart: animated draw-on-scroll (chart traces itself as section enters viewport)
  - X: dates (90 days), Y: health score
  - Fill: gradient teal (healthy periods) → rose (dip periods)
  - Critical events marked as dots on the line with labels (ticket spikes, sentiment drops)
  - Hover any point → tooltip with exact score + events that day
- Score Anatomy: 6 radial gauge meters in a row
  - Each: small donut chart (60px), score in center, label below
  - Animated fill on scroll-reveal
  - Color: gradient from emerald (full) to rose (empty)
- Risk Flags: vertical list, each flag has a rose dot + description + "since [date]"
  - Subtle slide-in animation, staggered 100ms per flag

**SECTION 3: DEPLOYMENT DNA (Scroll-reveal)**
- Header: "DEPLOYMENT DNA"
- Interactive node-link diagram (D3.js force-directed or custom):
  - Center node: Deployment Mode (e.g., "OVA")
  - Connected: Version, each Integration, each Constraint
  - Nodes: surface-far circles with labels inside
  - Edges: thin lines with --surface-border color
  - Hover node: highlights connected nodes, shows tooltip
  - Click integration node: "Find similar deployments" → RAG query

**SECTION 4: CUSTOMER JOURNEY (Scroll-reveal)**
- Header: "CUSTOMER JOURNEY"
- Horizontal scrollable timeline (overflow-x scroll with snap)
- Timeline line: thin horizontal, --surface-border color
- Events as nodes on the line:
  - Circle (12px) with connecting vertical line down to event card
  - Color: emerald (positive), --text-muted (neutral), rose (negative)
  - Each card below: date, event title, brief description
  - Events: Contract Start, First Scan, Milestones, Incidents, Current Status
- Timeline draws left-to-right as section scrolls into view
- Drag to scroll horizontally

**SECTION 5: INTELLIGENCE PANELS (Scroll-reveal)**
- Three equal columns:
  - **OPEN TICKETS:** List of tickets with severity ribbon + Jira ID + summary. Click → Ticket Detail.
  - **RECENT CALLS:** List of calls with mini sentiment wave + date + summary preview. Click → Insight Detail.
  - **SIMILAR ISSUES (RAG):** Matched past tickets from other customers, similarity % badge, resolution info.
- Each column: surface-near card, same height, content scrollable within

---

### 3.4 Agent Nexus

Full-viewport interactive neural network showing all 10 agents and their connections.

**Main Visualization (70% viewport):**
- Full-screen Three.js canvas (or high-quality D3 force-directed graph)
- Orchestrator: large center node, teal, pulsing
- Other 9 agents: arranged by lane in clusters
- Connection lines: animated particles traveling along them when data flows
- Node size: proportional to tasks_today
- Node pulse rate: proportional to current activity
- Lane color coding on each node
- Background: very subtle grid (wireframe plane beneath the graph)

**Agent Brain Panel (slides up from bottom on node click, 30% viewport height):**
- Frosted surface-near card, rounded top corners, drag handle to resize
- Three columns:
  - **Left (25%):** 3D animated agent icon (unique per agent — hexagon for Orchestrator, brain shape for Memory, eye for Health, etc.) + Status dot + "12 tasks today" + "98% success rate"
  - **Center (50%):** Reasoning Log — terminal-style scrolling text (IBM Plex Mono 400, text-sm, --text-primary on surface-far background). Auto-scrolls. Shows the agent's decision trail.
  - **Right (25%):** Mini stat gauges — Tasks Today (radial), Avg Response Time (number), Success Rate (horizontal bar), Last Active (timestamp)
- Panel slides up with spring animation (400ms, slight bounce)
- Click outside or drag down to dismiss

---

### 3.5 Signal Intelligence (Fathom Insights)

Call insights displayed with a waveform/radio signal aesthetic.

**Sentiment Spectrum (top, full-width, 200px height):**
- surface-near card
- Animated waveform (SVG or Canvas)
- Y-axis: sentiment score (-1 to +1)
- X-axis: date
- Wave line: gradient stroke from --bio-emerald (positive) through --text-ghost (neutral) to --bio-rose (negative)
- Background: subtle gradient glow matching the sentiment in each region
- Interactive: hover shows date/call count, click opens that call
- Drawing animation on page load (waveform traces itself left-to-right, 2s)

**Filter Bar:**
- Search + Customer dropdown + Sentiment filter (All/Positive/Neutral/Negative — each filter option has its colored dot) + Date range

**Insight Cards (stacked vertically, full-width):**
- surface-near card, full-width
- Top: Mini waveform decoration (Sentiment Wave component, 40×16px) + Customer name (Inter 600) + Date (IBM Plex Mono xs) + Sentiment indicator (colored dot + label)
- Participants: row of small avatar circles with names on hover
- Summary: Inter 400, text-base, 3 lines truncated with "Expand" toggle
- Action Items: checklist style
  - Each item: checkbox + task text + owner pill + deadline
  - Checkbox click → API call to toggle status
  - Overdue items: rose text + "OVERDUE" badge
- Decisions: Inter 400, text-sm, --text-primary
- Risks: rose-tinted surface-far pills
- Footer: [📋 Copy Recap] [📄 View Transcript] buttons — surface-far pill buttons with icon

**Action Tracker (floating side panel, right edge):**
- Fixed position, surface-near card, 260px width
- Header: "ACTION TRACKER"
- 3 stat rows: Pending (amber number), Overdue (rose number), Completed (emerald number)
- Scrollable list of action items below
- "View All →" link at bottom

---

### 3.6 Ticket Warroom

Dual-mode: Constellation (3D default) + Warroom Table (2D).

**Constellation View:**
- Three.js canvas, full section area
- See 3D-5 specification
- Filter pills floating at top: Status (colored dots), Severity, Customer, Type
- Toggle: "⚡ Constellation" / "📊 Warroom Table" — right side of filter bar

**Warroom Table View:**
- surface-near card with premium table
- Each row: severity ribbon (left edge, 3px colored bar), Jira ID (mono), Customer, Summary, Type icon, Severity dot, Status (animated micro progress bar), Assignee avatar, SLA countdown (IBM Plex Mono, ticking live), AI badge
- AI TRIAGED rows: subtle teal shimmer animation across the row (CSS gradient sweep)
- Row hover: translateY(-1px), glow border
- SLA column: live countdown timer (updates every second)
  - Green: > 50% time remaining
  - Amber: 20-50% remaining
  - Rose: < 20% or BREACHING (pulsing)
- Click row → Ticket Detail Drawer

**Ticket Detail Drawer (slides from right, 50% viewport width):**
- surface-near card, full viewport height
- Header: Jira ID + Customer + Severity + Status
- 3 stacked sections, each in surface-mid cards:
  1. **AI TRIAGE:** Category, severity recommendation, confidence (animated horizontal bar), suggested action, duplicate check result
  2. **AI DIAGNOSTICS:** Root cause, confidence bar, evidence list, next step
  3. **SIMILAR TICKETS (RAG):** Matched past tickets with similarity %, customer, resolution
- Close: X button or click outside drawer

---

### 3.7 Analytics Lab

Interactive data exploration with cross-filtering charts.

**KPI Row (top):** 4 Metric Orb fallbacks (2D circles) — Total Customers, Avg Health, Tickets Resolved, Calls Processed

**2×2 Chart Grid:**

**Chart 1 (Top-left): HEALTH HEATMAP**
- Calendar heatmap (like GitHub contributions)
- Rows = customers (10), Columns = days (30)
- Cell color: emerald (healthy) → amber → rose (at-risk)
- Hover cell: tooltip with exact score
- Click: cross-filter — highlights that customer in all other charts
- Animated fade-in on page load

**Chart 2 (Top-right): TICKET VELOCITY**
- Stacked area chart
- Layers: P1 (bottom, rose) → P2 (amber) → P3 (cyan) → P4 (slate, top)
- Smooth bezier curves, gradient fills
- Hover: vertical crosshair showing breakdown
- Click region: cross-filter to that time period

**Chart 3 (Bottom-left): SENTIMENT RIVER**
- Stream/river chart (ThemeRiver style)
- Width = call count at that sentiment level
- Color sections: emerald (positive), slate (neutral), rose (negative)
- Smooth, flowing, organic visualization
- Animated draw on scroll-reveal

**Chart 4 (Bottom-right): AGENT THROUGHPUT**
- Radial bar chart
- 10 rings (one per agent), each ring's length = tasks completed
- Ring color = agent lane color
- Center: total tasks number
- Animated fill on page load (rings grow outward)
- Hover ring: agent name + exact count

**Cross-Filtering:**
- Selecting data in any chart highlights corresponding data in ALL other charts
- Non-selected data dims to 20% opacity
- Clear selection: click empty area or "Reset" pill button

---

## 4. Transitions & Animations

### Page Transitions (Cinematic)
| From → To | Transition |
|-----------|-----------|
| Dashboard → Customers | Content scales down (0.95) + fades while Customer view scales up (1.05→1) + fades in. 500ms. |
| Customers → Customer Detail | Camera "fly-in" — selected card scales up and fills viewport while others blur and recede. 600ms. |
| Customer Detail → Back | Reverse fly-out — content shrinks back to card size. 500ms. |
| Any → Any (Orbital nav) | Current content fades + slides in direction of nav rotation. New content fades in from opposite. 400ms. |

### Scroll Animations (Customer Detail)
| Section | Animation | Trigger |
|---------|-----------|---------|
| Hero health ring | 3D ring starts spinning | On mount |
| Health chart | Line draws left-to-right | IntersectionObserver (threshold 0.3) |
| Score gauges | Fill animation | IntersectionObserver (threshold 0.5) |
| Risk flags | Stagger slide-in from left | IntersectionObserver (threshold 0.3) |
| Deployment DNA | Nodes fade in + connections draw | IntersectionObserver (threshold 0.3) |
| Journey timeline | Draw left-to-right | IntersectionObserver (threshold 0.2) |
| Intel panels | Slide up + fade in | IntersectionObserver (threshold 0.3) |

### Micro-Interactions
| Element | Interaction | Animation |
|---------|------------|-----------|
| Surface-interactive card | Hover | 3D tilt (rotateX/Y max 3deg from mouse pos) + glow border + lift. 300ms ease. |
| Orbital nav item | Click | Arc rotates, light beam transfers. 500ms cubic-bezier. |
| Button | Hover | Glow expansion from center outward. 200ms. |
| Nav item | Hover | Diagonal light sweep (shine passes across). 400ms. |
| Data point (chart) | Hover | Concentric ripple rings expand from point. 600ms. |
| Counter number | Mount | Rapid digit scramble → settle on final value. 2000ms. |
| Notification toast | Appear | Slide from top-right with particle trail. 300ms. |
| Notification toast | Dismiss | Particles scatter, opacity → 0. 400ms. |
| Detail drawer | Open | Slide from right + slight blur on background. 400ms spring. |
| Agent Brain panel | Open | Slide up from bottom with slight bounce. 400ms spring. |
| Empty state | Idle | Dormant visualization with faint outlines + floating text. Subtle pulse. |
| Loading skeleton | Active | Wave of teal-tinted light passing through. 1.5s loop. |

---

## 5. Responsive Behavior

### Breakpoints
- **Desktop Full (> 1440px):** All 3D elements active. Full Orbital nav. Max visual fidelity.
- **Desktop (1280-1440px):** 3D active but reduced particles. Full Orbital nav.
- **Laptop (1024-1280px):** 3D simplified (lower polygon count, fewer particles). Orbital nav.
- **Tablet (768-1024px):** 3D replaced with premium 2D fallbacks. Orbital nav → bottom tab bar (5 icons).
- **Mobile (< 768px):** Full 2D. Bottom tab bar. Cards stack vertically. Swipe between sections.

### 3D → 2D Fallback Strategy
| 3D Element | 2D Fallback |
|-----------|-------------|
| Neural Sphere | Static SVG network graph with animated connection lines (CSS) |
| Health Terrain | Heat map grid (colored cells) |
| Floating Orbs | Radial gradient circles with float animation |
| Data Flow Rivers | Animated SVG dots on paths |
| Ticket Constellation | Premium table view (default on tablet/mobile) |
| 3D Health Ring | SVG arc (already exists as component) |

### Accessibility
- **Reduce Motion toggle:** Settings page + respects `prefers-reduced-motion` media query
- When reduced motion: all 3D elements switch to 2D fallbacks, animations replaced with simple fades
- Color-blind safe: every status uses shape + icon + color (never color alone)
- Keyboard navigation: all 3D scenes have keyboard controls (arrow keys), Orbital nav supports left/right arrows
- Screen reader: all 3D canvases have aria-labels, interactive elements described

---

## 6. Technology Requirements for Frontend

### New Dependencies (beyond base React+Vite+Tailwind stack)
```
# 3D rendering
@react-three/fiber          # React renderer for Three.js
@react-three/drei           # Useful Three.js helpers (Html, OrbitControls, Sparkles, etc.)
three                       # Three.js core

# Animations
framer-motion               # Page transitions, scroll animations, layout animations
gsap                        # Complex timeline animations (sphere camera, page transitions)

# Charts
recharts                    # Health trend, ticket volume
d3                          # Sentiment river (stream graph), deployment DNA, heatmap

# Interactions
@dnd-kit/core               # Drag-and-drop (ticket board fallback)
@dnd-kit/sortable           # Sortable lists
fuse.js                     # Fuzzy search for command palette

# Scroll
@react-spring/web           # Spring physics animations (optional, framer-motion may cover)
```

### Performance Targets
- 3D scenes: 60fps on M1 MacBook / RTX 2060 equivalent
- Initial page load (with 3D): < 4 seconds
- Initial page load (2D fallback): < 2 seconds
- Three.js bundle: lazy-loaded (code-split), not in main bundle
- 3D loads after 2D skeleton renders (progressive enhancement)
