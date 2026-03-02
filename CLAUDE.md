# CLAUDE.md — CS Control Plane Development Context

> This file is the single source of truth for Claude Code when working on this project.
> Read this FIRST before making any changes to the codebase.

---

## Project Identity

- **Name:** HivePro CS Control Plane
- **Codename:** Mission Control
- **Type:** Full-stack web application (spatial dashboard + AI agent backend)
- **Author:** Ayushmaan Singh Naruka (AI Hub Team, HivePro)
- **Design Tier:** Premium enterprise — spatial 3D command center, NOT a traditional dashboard

---

## What This Project Does

The CS Control Plane is an AI-powered spatial dashboard that orchestrates 10 specialized agents to automate Customer Success workflows at HivePro. It replaces manual processes like call analysis, ticket triage, health monitoring, and report generation with an always-on virtual CS workforce.

**Core capabilities:**
1. **Agent Orchestration** — Routes events (Jira tickets, Fathom calls, cron jobs) to the correct AI agent via a central Orchestrator
2. **Customer Memory** — Maintains structured + semantic memory for every customer (PostgreSQL + ChromaDB)
3. **Spatial 3D Dashboard** — Immersive command center with 3D neural sphere, health terrain, floating orbs, particle rivers, and cinematic transitions
4. **AI Triage** — Auto-classifies and suggests actions for incoming Jira tickets
5. **Call Intelligence** — Extracts summaries, action items, sentiment from Fathom recordings
6. **Health Monitoring** — Calculates daily health scores, flags at-risk customers
7. **RAG-Powered Search** — Finds similar past issues across customers for faster resolution

---

## Documentation Reference

All project documentation lives in the `/docs` directory:

| Document | Path | Read When |
|----------|------|-----------|
| **PRD** | `/docs/PRD.md` | Understanding features, user stories, acceptance criteria |
| **Wireframes** | `/docs/WIREFRAMES.md` | Building any UI component — has 3D specs, colors, fonts, layouts, animations, responsive fallbacks |
| **API Contract** | `/docs/API_CONTRACT.md` | Building any API endpoint — has request/response JSON shapes |
| **Database Schema** | `/docs/DATABASE_SCHEMA.md` | Working with models, migrations, seed data |

**Read order for a new feature:** PRD (what) → Wireframes (how it looks) → API Contract (data shape) → Database Schema (storage)

---

## Tech Stack

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| **Frontend** | React | 18.x | |
| Build Tool | Vite | 5.x | |
| Styling | Tailwind CSS | 3.x | + custom CSS for void/glow effects |
| State Management | Zustand | 4.x | |
| Routing | React Router | 6.x | |
| HTTP Client | Axios | 1.x | |
| **3D Rendering** | Three.js | latest | Core 3D engine |
| 3D React Bindings | @react-three/fiber | latest | React renderer for Three.js |
| 3D Helpers | @react-three/drei | latest | Html, OrbitControls, Sparkles, etc. |
| **Animation** | Framer Motion | latest | Page transitions, scroll reveals, layout animations |
| Complex Timelines | GSAP | latest | 3D camera movements, sphere interactions |
| **Charts** | Recharts | 2.x | Health trend, ticket volume |
| Advanced Charts | D3 | 7.x | Heatmap, stream graph, force-directed graphs |
| **Interactions** | @dnd-kit/core + sortable | 6.x | Drag-and-drop (ticket board) |
| Fuzzy Search | fuse.js | latest | Command palette search |
| **Backend** | FastAPI | 0.109+ | |
| Database | PostgreSQL | 16 | |
| Vector DB | ChromaDB | 0.4+ | |
| ORM | SQLAlchemy | 2.0 | |
| Migrations | Alembic | 1.13+ | |
| Auth | python-jose (JWT) | 3.3+ | |
| Password | passlib[bcrypt] | 1.7+ | |
| Task Queue | Celery | 5.3+ | |
| Cache/Broker | Redis | 7.x | |
| LLM | Claude API | claude-sonnet-4-5-20250929 | |
| Browser Automation | Playwright (Python) | 1.40+ | |
| Testing | Pytest + Playwright | latest | |

---

## Project Structure

```
hivepro-cs-control-plane/
├── CLAUDE.md                          ← YOU ARE HERE
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml                 # PostgreSQL + Redis
│
├── docs/
│   ├── PRD.md
│   ├── WIREFRAMES.md
│   ├── API_CONTRACT.md
│   └── DATABASE_SCHEMA.md
│
├── backend/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry
│   │   ├── config.py                  # Settings from .env
│   │   ├── database.py                # PostgreSQL connection
│   │   ├── chromadb_client.py         # ChromaDB connection
│   │   ├── websocket_manager.py       # WebSocket broadcast
│   │   ├── models/                    # SQLAlchemy models (10 tables)
│   │   ├── schemas/                   # Pydantic schemas
│   │   ├── routers/                   # API endpoints
│   │   ├── agents/                    # AI agent implementations (10 agents)
│   │   ├── services/                  # Business logic
│   │   ├── tasks/                     # Celery async tasks
│   │   ├── middleware/auth.py         # JWT middleware
│   │   └── utils/
│   │       ├── security.py
│   │       └── seed.py                # Demo data seeder
│   └── tests/
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css                  # Void background, nebula mesh, depth vignette
│       │
│       ├── stores/                    # Zustand stores
│       │   ├── authStore.js
│       │   ├── dashboardStore.js
│       │   ├── customerStore.js
│       │   ├── agentStore.js
│       │   ├── ticketStore.js
│       │   ├── insightStore.js
│       │   ├── alertStore.js
│       │   └── websocketStore.js
│       │
│       ├── services/                  # API clients
│       │   ├── api.js                 # Axios instance
│       │   ├── authApi.js
│       │   ├── dashboardApi.js
│       │   ├── customerApi.js
│       │   ├── agentApi.js
│       │   ├── ticketApi.js
│       │   ├── insightApi.js
│       │   └── websocket.js           # WebSocket client
│       │
│       ├── three/                     # 3D scenes (code-split, lazy-loaded)
│       │   ├── NeuralSphere.jsx       # Hero 3D agent globe
│       │   ├── HealthTerrain.jsx      # 3D topographic map
│       │   ├── FloatingOrb.jsx        # Holographic metric orb
│       │   ├── DataFlowRivers.jsx     # Particle stream visualization
│       │   ├── TicketConstellation.jsx # 3D ticket star field
│       │   ├── HealthRing3D.jsx       # 3D rotating health torus
│       │   └── AgentIcon3D.jsx        # Unique 3D agent avatars
│       │
│       ├── components/
│       │   ├── layout/
│       │   │   ├── OrbitalNav.jsx     # Bottom arc navigation (replaces sidebar)
│       │   │   ├── TopBar.jsx         # Floating breadcrumb + actions
│       │   │   ├── CommandPalette.jsx  # Cmd+K global search
│       │   │   ├── NebulaBg.jsx       # Animated background mesh
│       │   │   └── ParticleField.jsx  # Canvas particle layer
│       │   │
│       │   ├── shared/
│       │   │   ├── SurfaceCard.jsx    # Frosted depth card (3 levels)
│       │   │   ├── StatusIndicator.jsx # Glowing dot + label
│       │   │   ├── HealthRing.jsx     # 2D SVG health ring
│       │   │   ├── AnimatedCounter.jsx # Slot-machine number scramble
│       │   │   ├── MetricOrb2D.jsx    # 2D fallback for floating orbs
│       │   │   ├── SentimentWave.jsx  # Mini waveform component
│       │   │   ├── SeverityMarker.jsx # Colored light ribbon
│       │   │   ├── EventPulseItem.jsx # Live feed item
│       │   │   └── LoadingSkeleton.jsx # Teal shimmer skeleton
│       │   │
│       │   ├── dashboard/
│       │   │   ├── NeuralSphereWrapper.jsx  # Suspense + lazy load 3D
│       │   │   ├── HealthTerrainWrapper.jsx # Suspense + lazy load 3D
│       │   │   ├── FloatingOrbsGrid.jsx     # 4 metric orbs positioned
│       │   │   ├── DataFlowRiversWrapper.jsx
│       │   │   ├── LivePulse.jsx            # EKG-style event timeline
│       │   │   └── QuickActions.jsx
│       │   │
│       │   ├── customers/
│       │   │   ├── SolarSystemView.jsx  # 3D orbital customer view
│       │   │   ├── PremiumGrid.jsx      # 3D-tilt cards
│       │   │   ├── DataTable.jsx        # Premium table
│       │   │   ├── QuickIntelPanel.jsx  # Hover/select summary
│       │   │   ├── CustomerHero.jsx     # Detail page hero section
│       │   │   ├── HealthStory.jsx      # Scroll-reveal charts
│       │   │   ├── DeploymentDNA.jsx    # Node-link diagram (D3)
│       │   │   ├── CustomerJourney.jsx  # Horizontal timeline
│       │   │   └── IntelPanels.jsx      # Tickets/Calls/RAG columns
│       │   │
│       │   ├── agents/
│       │   │   ├── NeuralNetwork.jsx    # Full neural graph visualization
│       │   │   ├── AgentBrainPanel.jsx  # Slide-up detail panel
│       │   │   └── ReasoningLog.jsx     # Terminal-style log
│       │   │
│       │   ├── insights/
│       │   │   ├── SentimentSpectrum.jsx # Full-width waveform chart
│       │   │   ├── InsightCard.jsx      # Individual call insight
│       │   │   └── ActionTracker.jsx    # Floating side panel
│       │   │
│       │   ├── tickets/
│       │   │   ├── ConstellationWrapper.jsx  # 3D star field
│       │   │   ├── WarroomTable.jsx          # Premium table view
│       │   │   └── TicketDetailDrawer.jsx    # Slide-in drawer
│       │   │
│       │   └── reports/
│       │       ├── HealthHeatmap.jsx    # Calendar heatmap (D3)
│       │       ├── TicketVelocity.jsx   # Stacked area chart
│       │       ├── SentimentRiver.jsx   # Stream graph (D3)
│       │       ├── AgentThroughput.jsx  # Radial bar chart (D3)
│       │       └── ReportList.jsx       # Report table + generate modal
│       │
│       └── pages/
│           ├── LoginPage.jsx
│           ├── DashboardPage.jsx       # Command Center
│           ├── CustomersPage.jsx       # Customer Observatory
│           ├── CustomerDetailPage.jsx  # Deep Dive (scroll journey)
│           ├── AgentsPage.jsx          # Agent Nexus
│           ├── InsightsPage.jsx        # Signal Intelligence
│           ├── TicketsPage.jsx         # Ticket Warroom
│           ├── ReportsPage.jsx         # Analytics Lab
│           └── SettingsPage.jsx        # Config + Reduce Motion toggle
│
└── e2e/
    ├── playwright.config.js
    └── tests/
```

---

## Architecture Rules

### Rule 1: Event-Driven Agent System
Everything flows through the Orchestrator. External events (Jira webhook, Fathom sync, cron) create an `events` record → Orchestrator reads it → routes to the correct agent → agent reads Customer Memory → executes → writes output → updates Customer Memory → broadcasts via WebSocket.

**Never** have agents directly call each other. Always go through the Orchestrator or event system.

### Rule 2: Customer Memory is the Single Source of Truth
Every agent reads from and writes to the Customer Memory (PostgreSQL + ChromaDB). No agent should maintain its own state about a customer.

### Rule 3: WebSocket for All Real-Time Updates
Any change that should appear immediately (agent status, new event, alert, health score) must broadcast via WebSocket. The frontend never polls.

### Rule 4: AI Calls are Always Async
All Claude API calls go through Celery tasks. The API returns 202 with a task_id. Results broadcast via WebSocket. Never block the API thread.

### Rule 5: 3D is Progressive Enhancement
Always build the 2D version first. 3D scenes are lazy-loaded (React.lazy + Suspense) and code-split into their own chunks. The app must be fully functional with 2D fallbacks. 3D enhances but never blocks.

### Rule 6: Spatial Depth Design
Three surface levels: near (0.65 opacity), mid (0.45), far (0.25). Critical data uses surface-near. Supporting data uses surface-mid/far. The void (#020408) is the true background. No flat white or gray backgrounds anywhere.

### Rule 7: Orbital Navigation
No sidebar. The Orbital Nav arc is the primary navigation at the bottom-center. Command Palette (Cmd+K) is the power-user alternative. Breadcrumbs float at top-left. Content fills the full viewport.

---

## Coding Standards

### Python (Backend)
```python
# Same as before — type hints, Pydantic schemas, HTTPException, dependency injection
# See API_CONTRACT.md for exact response shapes
```

### JavaScript/React (Frontend)
```javascript
// File naming: PascalCase.jsx for components, camelCase.js for utils/stores
// 3D components: /src/three/ directory, always lazy-loaded
// Animations: framer-motion for layout/page, gsap for 3D camera, CSS for micro-interactions

// 3D Scene Pattern:
const NeuralSphereWrapper = () => (
  <Suspense fallback={<NetworkGraphSVG />}>  {/* 2D fallback */}
    <Canvas camera={{ position: [0, 2, 5], fov: 60 }}>
      <NeuralSphere />
    </Canvas>
  </Suspense>
);

// Surface Card Pattern:
<SurfaceCard level="near" interactive>  {/* level: near | mid | far */}
  <h3>Card Title</h3>
</SurfaceCard>

// Animation Pattern (scroll reveal):
<motion.div
  initial={{ opacity: 0, y: 40 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true, margin: "-100px" }}
  transition={{ duration: 0.6, ease: "easeOut" }}
>
  <HealthStoryChart />
</motion.div>
```

### Import Order
1. React / Three.js / external libraries
2. Internal modules (stores, services, utils)
3. Components
4. Styles

---

## Design System Quick Reference

**Void:** #020408 (body bg — absolute black, not navy)
**Accents:** --bio-teal=#00F5D4, --bio-violet=#8B5CF6, --bio-cyan=#22D3EE
**Danger:** --bio-rose=#FB7185, Warning: --bio-amber=#FBBF24, Success: --bio-emerald=#34D399
**Surfaces:** near=rgba(8,16,32,0.65), mid=0.45, far=0.25 — all with backdrop-blur(20px)
**Fonts:** Space Grotesk (display/numbers), IBM Plex Mono (data/labels), Inter (body)
**Nav:** Orbital arc at bottom-center, NOT sidebar. Cmd+K palette.

**Full design system:** See WIREFRAMES.md Section 1

---

## Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/cs_control_plane
SYNC_DATABASE_URL=postgresql://postgres:password@localhost:5432/cs_control_plane

# Redis
REDIS_URL=redis://localhost:6379/0

# Auth
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Claude API
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# ChromaDB
CHROMADB_PATH=./chromadb_data

# External (Phase 2)
JIRA_API_URL=https://hivepro.atlassian.net
JIRA_API_TOKEN=
SLACK_BOT_TOKEN=
FATHOM_EMAIL=
FATHOM_PASSWORD=

# Frontend
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/api/ws
```

---

## Docker Compose

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: cs_control_plane
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

---

## Development Phases (Build Order)

### Phase 1: Foundation
- [ ] Project scaffolding (all folders, configs, .env, docker-compose)
- [ ] Docker Compose up (PostgreSQL + Redis)
- [ ] SQLAlchemy models for all 10 tables
- [ ] Alembic initial migration
- [ ] FastAPI skeleton with health check
- [ ] **Test:** `docker-compose up` → `alembic upgrade head` → tables created

### Phase 2: Auth + Users
- [ ] JWT auth (login, refresh, me)
- [ ] Auth middleware
- [ ] **Test:** Login → get token → hit /auth/me

### Phase 3: Customer CRUD + Health
- [ ] Customer CRUD + Health score endpoints
- [ ] **Test:** Create customer → add health score → get detail

### Phase 4: Core Services
- [ ] Claude API wrapper, ChromaDB + RAG, mock Jira/Fathom/Slack services
- [ ] **Test:** Embed document → query similarity → get results

### Phase 5: Agent Framework
- [ ] Base agent, Orchestrator, Memory Agent, Call Intel, Health Monitor
- [ ] Celery + Redis setup
- [ ] **Test:** Trigger health check → agent runs → score updated

### Phase 6: Event System + WebSocket
- [ ] Event model, routing logic, WebSocket manager
- [ ] **Test:** Create event → agent processes → WebSocket push

### Phase 7: Remaining Agents
- [ ] Ticket Triage, Troubleshooter, Escalation, QBR, SOW, Deployment Intel
- [ ] **Test:** Create ticket → auto-triage → result stored

### Phase 8: Frontend Shell — Design System + Navigation
- [ ] Vite + React + Tailwind + Router + Framer Motion setup
- [ ] Google Fonts (Space Grotesk, IBM Plex Mono, Inter)
- [ ] Global CSS: void background, nebula mesh, depth vignette, particle field
- [ ] SurfaceCard component (3 levels)
- [ ] StatusIndicator, HealthRing (2D), AnimatedCounter, SeverityMarker
- [ ] OrbitalNav (bottom arc navigation)
- [ ] CommandPalette (Cmd+K)
- [ ] TopBar (floating breadcrumb + icons)
- [ ] **Test:** App loads with void/nebula background, orbital nav works, Cmd+K opens palette

### Phase 9: Login + Command Center (2D first)
- [ ] Login page with auth flow
- [ ] Dashboard: 4 Metric Orbs (2D fallback first)
- [ ] Dashboard: Live Pulse (EKG timeline)
- [ ] Dashboard: Health grid (2D cards with health rings)
- [ ] Dashboard: WebSocket integration
- [ ] **Test:** Login → see dashboard with real data → events stream in

### Phase 10: Command Center 3D Upgrade
- [ ] Install Three.js + @react-three/fiber + @react-three/drei + gsap
- [ ] Neural Sphere (lazy-loaded, with Suspense + 2D fallback)
- [ ] Floating Orbs (3D, parallax)
- [ ] Data Flow Rivers (particle streams)
- [ ] Health Terrain (3D topo map)
- [ ] **Test:** 3D loads after skeleton → interactive → click agent node → detail

### Phase 11: Customer Observatory + Detail
- [ ] Customer Observatory: Premium Grid (3D tilt cards) + Data Table
- [ ] Solar System View (3D orbital — can defer to Phase 15 polish)
- [ ] Quick Intel Panel
- [ ] Customer Detail: Hero (3D health ring), Health Story (scroll charts), Deployment DNA (D3), Journey Timeline, Intel Panels
- [ ] **Test:** Browse → filter → click → scroll through detail → see RAG results

### Phase 12: Agent Nexus
- [ ] Neural network visualization (D3 force-directed or Three.js)
- [ ] Agent Brain Panel (slide-up)
- [ ] Reasoning Log (terminal style)
- [ ] **Test:** See agents → click → view reasoning → see data flow

### Phase 13: Signal Intelligence + Ticket Warroom
- [ ] Sentiment Spectrum waveform
- [ ] Insight cards with action tracking
- [ ] Warroom Table (premium table, live SLA countdown)
- [ ] Ticket Detail Drawer
- [ ] Ticket Constellation (3D — can defer to Phase 15)
- [ ] **Test:** Browse insights → toggle action → browse tickets → drag status

### Phase 14: Analytics Lab
- [ ] Health Heatmap (D3 calendar)
- [ ] Ticket Velocity (Recharts stacked area)
- [ ] Sentiment River (D3 stream graph)
- [ ] Agent Throughput (D3 radial bar)
- [ ] Cross-filtering between charts
- [ ] Report list + generate modal
- [ ] **Test:** View analytics → click chart → see cross-filter → generate report

### Phase 15: Seed Data + Polish
- [ ] Comprehensive seed script (10 customers, 50 tickets, 100 insights, etc.)
- [ ] Page transitions (Framer Motion AnimatePresence)
- [ ] Scroll animations (IntersectionObserver + Framer Motion)
- [ ] Loading skeletons (teal shimmer)
- [ ] Empty states (dormant visualizations)
- [ ] Toast notifications (particle trail)
- [ ] Solar System view (if deferred from Phase 11)
- [ ] Ticket Constellation (if deferred from Phase 13)
- [ ] Settings page with Reduce Motion toggle
- [ ] **Test:** Fresh seed → full demo walkthrough → all animations smooth

### Phase 16: E2E Testing + Performance
- [ ] Playwright E2E tests
- [ ] 3D performance audit (fps monitoring)
- [ ] Bundle size audit (3D chunks lazy-loaded)
- [ ] Lighthouse accessibility check
- [ ] **Test:** All tests pass → 60fps on target hardware → accessible

---

## Quick Commands for Claude Code

**Setup:**
```
"Set up the project scaffolding — create the folder structure, docker-compose.yml, requirements.txt, package.json with all dependencies including Three.js and Framer Motion. Reference CLAUDE.md for the exact structure."
```

**Design System:**
```
"Build the frontend design system. Read docs/WIREFRAMES.md Section 1 for exact colors, fonts, surfaces. Create index.css with void background, nebula mesh, vignette. Build SurfaceCard (3 levels), StatusIndicator, HealthRing (2D SVG), AnimatedCounter components."
```

**Navigation:**
```
"Build the OrbitalNav component. Read docs/WIREFRAMES.md Section 2 for specs. Curved arc at bottom-center, 7 items with perspective transform, active item centered and enlarged. Also build CommandPalette (Cmd+K) with fuzzy search using fuse.js."
```

**3D Scene:**
```
"Build the NeuralSphere 3D component. Read docs/WIREFRAMES.md Section 1.5 (3D-1) for full spec. Use @react-three/fiber + drei. IcosahedronGeometry wireframe, 10 agent nodes as emissive spheres, OrbitControls. Wrap in Suspense with SVG network graph as fallback."
```

**Backend feature:**
```
"Build the customer CRUD endpoints. Read docs/API_CONTRACT.md Section 3 for exact request/response formats, and docs/DATABASE_SCHEMA.md Section 2.2 for the model."
```

---

## Common Pitfalls — Do / Don't

| DO | DON'T |
|----|-------|
| Build 2D first, add 3D as progressive enhancement | Block the app on 3D loading |
| Lazy-load all Three.js scenes (React.lazy + Suspense) | Import Three.js in the main bundle |
| Use the three surface levels (near/mid/far) for depth | Use flat solid backgrounds |
| Use Space Grotesk for display, IBM Plex Mono for data | Use a single font everywhere |
| Use Orbital Nav at bottom-center | Build a sidebar |
| Animate with Framer Motion (layout) + GSAP (3D cameras) | Use CSS transitions for complex sequences |
| Use --bio-teal AND --bio-violet (two-tone accent) | Use only one accent color |
| Body background is #020408 (near-black void) | Use #080C14 or any navy (that was the old design) |
| Put async AI calls in Celery tasks | Block API threads with Claude API calls |
| Broadcast changes via WebSocket | Poll endpoints from frontend |
| Respect prefers-reduced-motion | Force 3D on all users |
| Use D3 for complex charts (heatmap, river, radial) | Try to force everything into Recharts |
