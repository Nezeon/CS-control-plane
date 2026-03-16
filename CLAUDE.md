# CLAUDE.md — CS Control Plane Development Context

> This file is the single source of truth for Claude Code when working on this project.
> Read this FIRST before making any changes to the codebase.

---

## Core Principles

1. First think through the problem, read the codebase for relevant files.
2. Before you make any major changes, check in with me and I will verify the plan.
3. Please every step of the way just give me a high level explanation of what changes you made
4. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
5. Maintain a documentation file that describes how the architecture of the app works inside and out.
6. Never speculate about code you have not opened. If the user references a specific file, you MUST read the file before answering. Make sure to investigate and read relevant files BEFORE answering questions about the codebase. Never make any claims about code before investigating unless you are certain of the correct answer - give grounded and hallucination-free answers.

---

## Project Identity

- **Name:** HivePro CS Control Plane
- **Codename:** Mission Control
- **Type:** Full-stack web application (spatial dashboard + AI agent backend)
- **Author:** Ayushmaan Singh Naruka (AI Hub Team, HivePro)
- **Design Tier:** Premium enterprise — spatial 3D command center, NOT a traditional dashboard

---

## What This Project Does

The CS Control Plane is an AI-powered spatial dashboard that orchestrates **13 named AI agents in a 4-tier hierarchy** (Supervisor → Lane Leads → Specialists → Foundation) to automate Customer Success workflows at HivePro. Each agent has a human identity, personality, specialized traits, and tools — running multi-round pipelines instead of single-shot API calls.

**Core capabilities:**
1. **4-Tier Agent Hierarchy** — A Supervisor (Naveen Kapoor, T1) delegates to 3 Lane Leads (T2: Rachel Torres/Support, Damon Reeves/Value, Priya Mehta/Delivery), who coordinate 8 Specialists (T3), all powered by a Foundation memory layer (Atlas, T4)
2. **Multi-Round Pipeline Execution** — Agents think in stages: perceive → retrieve → think → act → reflect → quality_gate → finalize, with tier-specific configurations defined in YAML
3. **3-Tier Memory System** — Working memory (in-process scratchpad), episodic memory (ChromaDB per-agent diary), semantic memory (ChromaDB lane-scoped knowledge pools)
4. **Inter-Agent Message Board** — Typed messages (task_assignment, deliverable, request, escalation, feedback) flowing through the hierarchy with threading and delegation chains
5. **12+ Agent Tools** — Agents call real functions (query_customer_db, search_similar_tickets, check_sla_status, publish_knowledge, etc.) via Claude's tool_use API
6. **YAML-Driven Configuration** — Agent personalities, traits, pipeline stages, org structure, and workflows defined in config files (not hardcoded Python)
7. **Spatial 3D Dashboard** — Immersive command center with 3D neural sphere (13 agents in 4 tiers), health terrain, floating orbs, particle rivers, and cinematic transitions
8. **AI Triage** — Auto-classifies and suggests actions for incoming Jira tickets
9. **Call Intelligence** — Extracts summaries, action items, sentiment from Fathom recordings via API
10. **Health Monitoring** — Calculates daily health scores, flags at-risk customers
11. **RAG-Powered Search** — Finds similar past issues across customers for faster resolution

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
| Config | PyYAML | 6.0+ | Agent profiles, org structure, pipelines, workflows |
| HTTP Client | httpx | 0.27+ | Fathom API integration |
| Browser Automation | Playwright (Python) | 1.40+ | |
| Testing | Pytest + Playwright | latest | |

---

## Project Structure

```
hivepro-cs-control-plane/
├── CLAUDE.md                          ← YOU ARE HERE
├── REBUILD_PLAN.md                    # Master rebuild plan (source of truth for architecture)
├── .env.example
├── .gitignore
├── README.md
├── render.yaml                        # Render deployment config
│
├── docs/
│   ├── PRD.md
│   ├── WIREFRAMES.md
│   ├── API_CONTRACT.md
│   └── DATABASE_SCHEMA.md
│
├── backend/
│   ├── requirements.txt
│   ├── Procfile                       # Render process config
│   ├── runtime.txt                    # Python version
│   ├── alembic.ini
│   ├── alembic/versions/
│   │
│   ├── config/                        # YAML-driven agent configuration
│   │   ├── org_structure.yaml         # 4-tier hierarchy, lanes, reporting lines
│   │   ├── agent_profiles.yaml        # 13 agent identities, personalities, traits, tools
│   │   ├── pipeline.yaml              # Pipeline stage definitions per tier
│   │   └── workflows.yaml             # Event → agent routing workflows
│   │
│   ├── app/
│   │   ├── main.py                    # FastAPI entry
│   │   ├── config.py                  # Settings from .env
│   │   ├── database.py                # PostgreSQL connection
│   │   ├── chromadb_client.py         # ChromaDB connection
│   │   ├── websocket_manager.py       # WebSocket broadcast
│   │   │
│   │   ├── models/                    # SQLAlchemy models (12 tables)
│   │   │   ├── ...                    # Existing 10 tables (users, customers, health_scores, etc.)
│   │   │   ├── execution_round.py     # agent_execution_rounds table
│   │   │   └── agent_message.py       # agent_messages table
│   │   │
│   │   ├── schemas/                   # Pydantic schemas
│   │   │   ├── ...                    # Existing schemas
│   │   │   ├── pipeline.py            # Pipeline execution schemas
│   │   │   ├── message.py             # Agent message schemas
│   │   │   ├── memory.py              # Memory API schemas
│   │   │   └── hierarchy.py           # Hierarchy API schemas
│   │   │
│   │   ├── routers/                   # API endpoints
│   │   │   ├── ...                    # Existing routers (auth, customers, dashboard, etc.)
│   │   │   ├── webhooks.py            # Fathom webhook receiver
│   │   │   ├── pipeline.py            # /v2/pipeline/* endpoints
│   │   │   ├── messages.py            # /v2/messages/* endpoints
│   │   │   ├── memory.py              # /v2/memory/* endpoints
│   │   │   ├── hierarchy.py           # /v2/hierarchy/* endpoints
│   │   │   └── workflows.py           # /v2/workflows/* endpoints
│   │   │
│   │   ├── agents/                    # AI agent implementations (13 agents)
│   │   │   ├── base_agent.py          # Base agent with pipeline execution
│   │   │   ├── pipeline_engine.py     # Multi-round pipeline runner
│   │   │   ├── orchestrator.py        # Naveen Kapoor (T1 Supervisor)
│   │   │   ├── leads/                 # Tier 2 Lane Leads
│   │   │   │   ├── support_lead.py    # Rachel Torres
│   │   │   │   ├── value_lead.py      # Damon Reeves
│   │   │   │   └── delivery_lead.py   # Priya Mehta
│   │   │   ├── specialists/           # Tier 3 Specialists (existing agents, upgraded)
│   │   │   │   ├── triage_agent.py    # Kai Nakamura
│   │   │   │   ├── troubleshooter.py  # Leo Petrov
│   │   │   │   ├── escalation_agent.py # Maya Santiago
│   │   │   │   ├── health_monitor.py  # Dr. Aisha Okafor
│   │   │   │   ├── call_intel.py      # Jordan Ellis
│   │   │   │   ├── qbr_agent.py       # Sofia Marquez
│   │   │   │   ├── sow_agent.py       # Ethan Brooks
│   │   │   │   └── deployment_intel.py # Zara Kim
│   │   │   ├── memory/                # Tier 4 Foundation + Memory system
│   │   │   │   ├── customer_memory.py # Atlas — Customer Memory Manager
│   │   │   │   ├── working_memory.py  # In-process scratchpad
│   │   │   │   ├── episodic_memory.py # ChromaDB per-agent diary
│   │   │   │   └── semantic_memory.py # ChromaDB lane-scoped knowledge pools
│   │   │   ├── tools/                 # 12+ tool definitions for Claude tool_use
│   │   │   │   ├── tool_registry.py   # Tool registration and dispatch
│   │   │   │   ├── db_tools.py        # query_customer_db, query_health_scores, get_ticket_details
│   │   │   │   ├── rag_tools.py       # search_similar_tickets, search_knowledge_base
│   │   │   │   ├── action_tools.py    # write_report, create_action_item, send_alert
│   │   │   │   └── agent_tools.py     # read_agent_output, publish_knowledge, check_sla_status
│   │   │   ├── traits/                # 9+ pluggable trait behaviors
│   │   │   │   ├── trait_registry.py  # Trait registration and lifecycle hooks
│   │   │   │   ├── confidence_scoring.py
│   │   │   │   ├── escalation_detection.py
│   │   │   │   ├── sla_awareness.py
│   │   │   │   ├── strategic_oversight.py
│   │   │   │   ├── quality_evaluation.py
│   │   │   │   ├── delegation.py
│   │   │   │   ├── workflow_coordination.py
│   │   │   │   ├── synthesis.py
│   │   │   │   └── customer_sentiment.py
│   │   │   └── message_board.py       # Inter-agent message bus
│   │   │
│   │   ├── services/                  # Business logic
│   │   │   ├── ...                    # Existing services
│   │   │   └── fathom_service.py      # Fathom API client (httpx-based)
│   │   │
│   │   ├── tasks/                     # Celery async tasks
│   │   ├── middleware/auth.py         # JWT middleware
│   │   └── utils/
│   │       ├── security.py
│   │       └── seed.py                # Demo data seeder (expanded for new entities)
│   └── tests/
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── vercel.json                    # Vercel deployment config
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
│       │   ├── agentStore.js          # Updated: hierarchy, profiles, tier data
│       │   ├── ticketStore.js
│       │   ├── insightStore.js
│       │   ├── alertStore.js
│       │   ├── pipelineStore.js       # NEW: pipeline executions, active runs
│       │   ├── messageStore.js        # NEW: inter-agent messages, threads
│       │   ├── memoryStore.js         # NEW: episodic + semantic memory browsing
│       │   ├── reportStore.js
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
│       │   ├── pipelineApi.js         # NEW: /v2/pipeline/* calls
│       │   ├── messageApi.js          # NEW: /v2/messages/* calls
│       │   ├── memoryApi.js           # NEW: /v2/memory/* calls
│       │   ├── hierarchyApi.js        # NEW: /v2/hierarchy/* calls
│       │   ├── workflowApi.js         # NEW: /v2/workflows/* calls
│       │   └── websocket.js           # WebSocket client (extended events)
│       │
│       ├── three/                     # 3D scenes (code-split, lazy-loaded)
│       │   ├── NeuralSphere.jsx       # Hero 3D globe (13 agents, 4 tiers)
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
│       │   │   ├── LoadingSkeleton.jsx # Teal shimmer skeleton
│       │   │   ├── PipelineStageCard.jsx  # NEW: single pipeline stage display
│       │   │   ├── MessageThread.jsx      # NEW: threaded message chain
│       │   │   ├── MemoryEntry.jsx        # NEW: memory item card
│       │   │   ├── HierarchyNode.jsx      # NEW: agent tree node
│       │   │   ├── TraitBadge.jsx         # NEW: agent trait pill
│       │   │   └── AgentAvatar.jsx        # NEW: per-agent icon + tier ring
│       │   │
│       │   ├── dashboard/
│       │   │   ├── NeuralSphereWrapper.jsx  # Suspense + lazy load 3D
│       │   │   ├── HealthTerrainWrapper.jsx # Suspense + lazy load 3D
│       │   │   ├── FloatingOrbsGrid.jsx     # 4 metric orbs positioned
│       │   │   ├── DataFlowRiversWrapper.jsx
│       │   │   ├── ActivePipelinesStrip.jsx # NEW: live pipeline progress
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
│       │   │   ├── HierarchyTree.jsx      # 4-tier hierarchical tree (replaces NeuralNetwork)
│       │   │   ├── AgentBrainPanel.jsx    # Slide-up detail panel (expanded)
│       │   │   ├── AgentProfileCard.jsx   # Full/compact/node agent card
│       │   │   ├── ReasoningLog.jsx       # Terminal-style log
│       │   │   ├── PipelineView.jsx       # Active + recent pipeline executions
│       │   │   ├── MessageBoardView.jsx   # Message feed + thread detail
│       │   │   ├── MemoryInspector.jsx    # Episodic timeline + semantic browser
│       │   │   ├── ExecutionTraceView.jsx # Stage-by-stage drilldown
│       │   │   ├── WorkflowViewer.jsx     # Workflow diagram + active instances
│       │   │   └── AgentNexusTabs.jsx     # Sub-view tab bar
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
│       │       ├── AgentThroughput.jsx  # Radial bar chart (D3, now 13 agents)
│       │       └── ReportList.jsx       # Report table + generate modal
│       │
│       └── pages/
│           ├── LoginPage.jsx
│           ├── DashboardPage.jsx       # Command Center
│           ├── CustomersPage.jsx       # Customer Observatory
│           ├── CustomerDetailPage.jsx  # Deep Dive (scroll journey)
│           ├── AgentsPage.jsx          # Agent Nexus (with 6 sub-view tabs)
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
Any change that should appear immediately (agent status, new event, alert, health score, pipeline progress, delegation) must broadcast via WebSocket. The frontend never polls. New event types: `pipeline:*`, `delegation:*`, `memory:*`.

### Rule 4: AI Calls are Always Async
All Claude API calls go through Celery tasks. The API returns 202 with a task_id. Results broadcast via WebSocket. Never block the API thread.

### Rule 5: 3D is Progressive Enhancement
Always build the 2D version first. 3D scenes are lazy-loaded (React.lazy + Suspense) and code-split into their own chunks. The app must be fully functional with 2D fallbacks. 3D enhances but never blocks.

### Rule 6: Spatial Depth Design
Three surface levels: near (0.65 opacity), mid (0.45), far (0.25). Critical data uses surface-near. Supporting data uses surface-mid/far. The void (#020408) is the true background. No flat white or gray backgrounds anywhere.

### Rule 7: Orbital Navigation
No sidebar. The Orbital Nav arc is the primary navigation at the bottom-center. Command Palette (Cmd+K) is the power-user alternative. Breadcrumbs float at top-left. Content fills the full viewport.

### Rule 8: Hierarchical Delegation
Tasks flow DOWN the hierarchy: Supervisor (T1) → Lane Lead (T2) → Specialist (T3). Results flow UP. Specialists NEVER delegate to each other directly — sideways requests go through the Message Board and the Lane Lead coordinates. The Foundation layer (T4) serves ALL tiers.

### Rule 9: YAML-Driven Configuration
Agent identities, personalities, traits, tools, pipeline stages, org structure, and workflows are defined in YAML config files (`backend/config/`). **Never** hardcode agent behavior in Python. The code reads YAML at startup and constructs agents dynamically. To change an agent's behavior, edit YAML, not code.

### Rule 10: Message Board Communication
Agents communicate through typed messages on the Message Board (`agent_messages` table). Five message types: `task_assignment` (down), `deliverable` (up), `request` (sideways), `escalation` (up, urgent), `feedback` (down). Messages support threading via `thread_id` and `parent_id`. Every message links to its originating event.

### Rule 11: 3-Tier Memory System
Every agent accesses three memory tiers: **Working** (in-process scratchpad, cleared per run), **Episodic** (ChromaDB `episodic_memory` collection, per-agent diary with tri-factor retrieval), **Semantic** (ChromaDB `shared_knowledge` collection, lane-scoped knowledge pools). Agents read episodic + semantic during `retrieve` stage, write to episodic during `reflect` stage, and optionally publish to semantic via `publish_knowledge` tool.

### Rule 12: Pipeline Execution
Every agent runs a multi-round pipeline defined in `pipeline.yaml`. Stages: `perceive` → `retrieve` → `think` → `act` → `reflect` → `quality_gate` → `finalize`. Each stage is logged to `agent_execution_rounds` with tools called, tokens used, confidence, and duration. The pipeline engine handles quality gate failures (retry from a specific stage). Every stage broadcasts progress via WebSocket.

---

## Coding Standards

### Python (Backend)
```python
# Type hints, Pydantic schemas, HTTPException, dependency injection
# See API_CONTRACT.md for exact response shapes

# YAML Profile Loading Pattern:
import yaml
from pathlib import Path

def load_agent_profiles() -> dict:
    config_path = Path(__file__).parent.parent.parent / "config" / "agent_profiles.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

# Tool Definition Pattern (for Claude tool_use):
def query_customer_db(customer_id: str) -> dict:
    """Look up customer profile and history."""
    # Tool functions are registered in tool_registry.py
    # They return dicts that Claude can use as tool_result
    customer = db.query(Customer).filter_by(id=customer_id).first()
    return {"name": customer.name, "health_score": customer.current_health, ...}

# Pipeline Stage Method Pattern:
class BaseAgent:
    async def perceive(self, context: WorkingMemory) -> WorkingMemory:
        """Process raw input into structured understanding."""
        ...
    async def retrieve(self, context: WorkingMemory) -> WorkingMemory:
        """Fetch relevant episodic + semantic memories."""
        ...
    async def think(self, context: WorkingMemory) -> WorkingMemory:
        """Reason about the task using Claude with tool_use."""
        ...
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
**Tiers:** T1=#00F5D4 (teal), T2=#8B5CF6 (violet), T3=#22D3EE (cyan), T4=#64748B (slate)
**Lanes:** Control=#00F5D4, Support=#FBBF24, Value=#34D399, Delivery=#22D3EE
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

# External Integrations
JIRA_API_URL=https://hivepro.atlassian.net
JIRA_API_TOKEN=
SLACK_BOT_TOKEN=
FATHOM_API_KEY=                        # Fathom API key (replaces email/password auth)
FATHOM_WEBHOOK_SECRET=                 # HMAC secret for Fathom webhook verification

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

> **Phase 0 is complete.** Phases A-H are the new architecture rebuild.

### Phase 0: Fathom Integration (COMPLETE)
- [x] Fathom API service (httpx-based, replaces Playwright scraping)
- [x] Webhook receiver endpoint (`POST /webhooks/fathom`)
- [x] Render + Vercel deployment configs
- [x] Environment variable updates (FATHOM_API_KEY replaces email/password)

### Phase A: Documentation Update (CURRENT)
- [x] Rewrite `/docs/PRD.md` — 13 agents, 4-tier hierarchy, features F12-F16
- [x] Rewrite `/docs/DATABASE_SCHEMA.md` — new tables + ChromaDB collections + YAML schemas
- [x] Rewrite `/docs/API_CONTRACT.md` — v2 endpoints for pipeline, messages, memory, hierarchy, workflows
- [x] Rewrite `/docs/WIREFRAMES.md` — hierarchy tree, 5 new Agent Nexus sub-views, new components
- [x] Update `CLAUDE.md` — new structure, rules 8-12, coding patterns, phases

### Phase B: Foundation
- [ ] Create `backend/config/` with 4 YAML files (org_structure, agent_profiles, pipeline, workflows)
- [ ] YAML config loader utility
- [ ] New SQLAlchemy models: `agent_execution_rounds`, `agent_messages`
- [ ] Alembic migration for new tables
- [ ] New ChromaDB collections: `episodic_memory`, `shared_knowledge`
- [ ] New Pydantic schemas: pipeline, message, memory, hierarchy
- [ ] **Test:** `alembic upgrade head` → 12 tables created, YAML loads without errors

### Phase C: Pipeline Engine + Tools
- [ ] Base agent with pipeline execution (`base_agent.py`, `pipeline_engine.py`)
- [ ] Tool registry + 12 tool definitions (db_tools, rag_tools, action_tools, agent_tools)
- [ ] Working memory implementation
- [ ] Episodic memory read/write (ChromaDB with tri-factor retrieval)
- [ ] Semantic memory read/write (lane-scoped knowledge pools)
- [ ] `agent_execution_rounds` logging for each pipeline stage
- [ ] WebSocket broadcasting per pipeline stage
- [ ] **Test:** Trigger agent → pipeline runs 7 stages → each logged → WebSocket events fire

### Phase D: Traits + Reflection
- [ ] Trait registry with lifecycle hooks (on_perceive, on_think, on_act, on_round_end, on_complete)
- [ ] 9 trait implementations: confidence_scoring, escalation_detection, sla_awareness, strategic_oversight, quality_evaluation, delegation, workflow_coordination, synthesis, customer_sentiment
- [ ] Reflection engine with tier-appropriate depth
- [ ] Quality gate with retry logic
- [ ] **Test:** Agent with traits → traits fire at correct stages → reflection writes to episodic memory

### Phase E: Message Board + Hierarchy
- [ ] Message board implementation (agent_messages CRUD)
- [ ] 5 message types with threading (task_assignment, deliverable, request, escalation, feedback)
- [ ] Delegation chain tracking
- [ ] New API routers: `/v2/pipeline/`, `/v2/messages/`, `/v2/memory/`, `/v2/hierarchy/`, `/v2/workflows/`
- [ ] Workflow YAML configs and routing logic
- [ ] **Test:** T1 delegates → T2 routes → T3 executes → deliverables flow back up

### Phase F: Agent Implementation
- [ ] Orchestrator (Naveen Kapoor, T1) — strategic decomposition, delegation, quality evaluation, synthesis
- [ ] 3 Lane Leads (T2) — Rachel Torres, Damon Reeves, Priya Mehta — workflow coordination, sub-delegation
- [ ] Migrate 8 existing Specialists (T3) to pipeline-based execution with traits and tools
- [ ] Upgrade Memory Agent (T4, Atlas) — context provider for all tiers
- [ ] **Test:** End-to-end: event → T1 → T2 → T3 → deliverables → T1 synthesis → output

### Phase G: Frontend — Agent Nexus Rebuild + New Views
- [ ] Agent Nexus redesign: HierarchyTree component (4-tier tree replacing flat network)
- [ ] Agent Nexus sub-view tabs: Hierarchy, Pipeline, Messages, Memory, Traces, Workflows
- [ ] PipelineView: active executions + recent completions with real-time WebSocket
- [ ] MessageBoardView: message feed (60%) + thread detail (40%)
- [ ] MemoryInspector: episodic timeline + semantic knowledge pool browser
- [ ] ExecutionTraceView: stage-by-stage drilldown with input/output/tools
- [ ] WorkflowViewer: workflow diagram + active instances
- [ ] New shared components: PipelineStageCard, MessageThread, MemoryEntry, HierarchyNode, TraitBadge, AgentAvatar, AgentProfileCard
- [ ] Dashboard: ActivePipelinesStrip (below Data Flow Rivers)
- [ ] NeuralSphere update: 13 agents in 4 tiers
- [ ] AgentThroughput chart: 13 rings grouped by tier
- [ ] New stores: pipelineStore, messageStore, memoryStore
- [ ] New API services: pipelineApi, messageApi, memoryApi, hierarchyApi, workflowApi
- [ ] **Test:** Full Agent Nexus walkthrough — hierarchy → pipeline → messages → memory → traces → workflows

### Phase H: Integration, Seed Data + Polish
- [ ] Expanded seed script: 10 customers, 50 tickets, 100 insights, 50 execution rounds, 40 messages, 30 episodic memories, 15 knowledge entries
- [ ] End-to-end integration testing (event → full pipeline → frontend updates)
- [ ] Page transitions for Agent Nexus sub-views
- [ ] Loading states for all new views
- [ ] WebSocket reconnection + buffering for pipeline events
- [ ] Playwright E2E tests for new views
- [ ] Performance audit (3D 60fps, WebSocket throughput, bundle size)
- [ ] **Test:** Fresh seed → full demo walkthrough → all features functional

---

## Quick Commands for Claude Code

**Phase B Foundation:**
```
"Create the 4 YAML config files in backend/config/. Read REBUILD_PLAN.md Section 4.2 for exact shapes. Also create the YAML loader utility and new SQLAlchemy models (agent_execution_rounds, agent_messages). Run alembic migration."
```

**Pipeline Engine:**
```
"Build the pipeline engine. Read docs/PRD.md Section 5.2 and REBUILD_PLAN.md Section 4.3. Create base_agent.py with 7 pipeline stage methods and pipeline_engine.py that runs stages in order, logs to agent_execution_rounds, and broadcasts via WebSocket."
```

**Tool Registry:**
```
"Build the tool registry and 12 tool definitions. Read REBUILD_PLAN.md Section 4.4 for the full tool list. Create tool_registry.py + db_tools.py + rag_tools.py + action_tools.py + agent_tools.py. Each tool returns a dict for Claude tool_result."
```

**Agent Nexus Frontend:**
```
"Rebuild the Agent Nexus page. Read docs/WIREFRAMES.md Sections 3.4 and 3.8-3.13 for layouts. Create HierarchyTree (4-tier tree), AgentNexusTabs (6 sub-views), and the Pipeline/Messages/Memory/Traces/Workflows sub-view components."
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
| Define agent behavior in YAML config files | Hardcode agent personalities/traits/tools in Python |
| Route tasks through hierarchy (T1→T2→T3) | Let specialists call each other directly |
| Use typed messages (task_assignment, deliverable, etc.) | Send unstructured strings between agents |
| Run agents through full pipeline (perceive→...→finalize) | Use single-shot Claude API calls for agent work |
| Log every pipeline stage to agent_execution_rounds | Skip execution logging (breaks trace viewer) |
| Use tri-factor retrieval for episodic memory | Use simple vector similarity only |
| Thread all messages with thread_id + parent_id | Create orphaned messages without thread context |
| Use tier colors (T1=teal, T2=violet, T3=cyan, T4=slate) | Use random colors for agent hierarchy |
