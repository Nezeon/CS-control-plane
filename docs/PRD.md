# HivePro CS Control Plane — Product Requirements Document (PRD)

**Product Name:** CS Control Plane  
**Codename:** Mission Control  
**Author:** Ayushmaan Singh Naruka (AI Hub Team)  
**Version:** 2.0 (Premium Redesign)  
**Date:** February 27, 2026  
**Status:** Pre-Development

---

## 1. Product Overview

### 1.1 One-Liner

CS Control Plane is HivePro's AI-powered spatial command center that orchestrates 10 specialized agents to automate the entire customer success lifecycle — visualized through an immersive 3D dashboard with real-time neural networks, health terrains, and cinematic data flows.

### 1.2 Problem Statement

HivePro's Customer Success team faces six critical pain points:

1. **Fathom recordings go unanalyzed** — Rich call data exists but nobody has bandwidth to extract insights, action items, or sentiment signals from every recording.
2. **Jira ticket overload** — Tickets pile up without intelligent triage, categorization, or duplicate detection. Engineers waste time re-diagnosing known issues.
3. **No centralized health tracking** — At-risk customers are identified too late because health signals are scattered across tools.
4. **Manual pre-meeting preparation** — CS consultants spend 30-60 minutes before each call gathering context.
5. **No cross-customer pattern recognition** — Recurring issues aren't identified or leveraged across customers.
6. **QBR preparation is time-consuming** — Monthly/quarterly reviews require manually compiling data.

### 1.3 Solution

A full-stack web application serving as a spatial control plane for 10 AI agents organized in 3 operational lanes (Delivery, Run/Support, Value). The application features:

- **Spatial 3D dashboard** — Neural sphere agent visualization, health terrain maps, floating metric orbs, particle data flow rivers
- **Orbital navigation** — Bottom-arc HUD replacing traditional sidebars, with Cmd+K command palette
- **Real-time WebSocket updates** — Every agent action, alert, and metric change streams live
- **Premium visual design** — "Deep Ocean Bioluminescence" aesthetic with two-tone accent system (teal + violet), frosted depth surfaces, cinematic page transitions

### 1.4 Target Users

| User | Role | Primary Use |
|------|------|-------------|
| CS Engineers | Day-to-day support | Ticket triage results, troubleshooting suggestions, customer context |
| CS Consultants | Customer-facing | Pre-meeting briefs, call insights, action item tracking |
| CS Managers | Team oversight | Health dashboard, risk alerts, performance metrics |
| VP/Directors | Executive oversight | QBR reports, aggregate analytics, system ROI |
| AI Hub Team | System admins | Agent monitoring, configuration, debugging |

---

## 2. Feature Requirements

### 2.1 MVP Features (Phase 1)

#### F1: Authentication & Authorization
- JWT-based login with role-based access control (admin, cs_manager, cs_engineer, viewer)
- **Acceptance Criteria:**
  - Login returns access (15min) + refresh (7d) JWT tokens
  - Protected endpoints return 401 for unauthenticated users
  - Role-based middleware restricts admin-only endpoints
  - Passwords hashed with bcrypt

#### F2: Command Center Dashboard (Spatial)
- Central mission control — immersive full-viewport view with 3D elements
- **User Stories:**
  - As a CS manager, I see the overall health of our portfolio the moment I log in, through an immersive 3D visualization
  - As any user, I see agents as glowing nodes on a rotating sphere with live data pulses
  - As any user, I see events flowing as particle streams through the system
- **Acceptance Criteria:**
  - 4 Floating Metric Orbs (3D holographic spheres with parallax) showing Total Customers, At-Risk, Open Tickets, Avg Health
  - Neural Sphere: 3D rotating globe with 10 agent nodes, pulsing connections, click-to-zoom agent detail
  - Data Flow Rivers: particle streams showing event routing from sources through Orchestrator to agents
  - Health Terrain: 3D topographic map — customer health as peaks/valleys, interactive
  - Live Pulse: EKG-style event timeline (not a list)
  - All real-time via WebSocket
  - 2D fallbacks for all 3D elements (progressive enhancement)
  - Orbital Nav at bottom-center for navigation

#### F3: Customer Observatory
- Portfolio view with three modes: Solar System (3D), Premium Grid (2D), Data Table
- **Acceptance Criteria:**
  - Solar System: customers as orbiting planets by tier, size by importance, color by health
  - Premium Grid: cards with 3D tilt on hover, health rings, severity ribbons
  - Data Table: sortable columns, row hover lift effect
  - Quick Intel Panel: appears on customer hover/select with summary stats + "Deep Dive" link
  - Search + filters (risk level, CS owner, sort)
  - View toggle between all three modes

#### F4: Customer Deep Dive (Scroll Journey)
- Immersive vertical scroll experience through a customer's complete story
- **Acceptance Criteria:**
  - Hero section: customer name in large display type, 3D rotating health ring, key stats
  - Health Story: animated area chart (draws on scroll), 6 radial gauge meters, risk flags
  - Deployment DNA: interactive node-link diagram showing tech setup
  - Customer Journey: horizontal scrollable timeline of all significant events
  - Intelligence Panels: 3 columns (Open Tickets, Recent Calls, Similar Issues via RAG)
  - All sections animate/reveal on scroll (IntersectionObserver)

#### F5: Agent Nexus
- Interactive neural network visualization of all 10 agents
- **Acceptance Criteria:**
  - Full-viewport graph: Orchestrator center, agents clustered by lane
  - Animated particles flow along connections during data routing
  - Node size = tasks today, pulse rate = current activity
  - Click agent → Agent Brain Panel slides up with: 3D avatar, reasoning log (terminal-style), mini stat gauges
  - Real-time status via WebSocket

#### F6: Signal Intelligence (Fathom Insights)
- Call insights with waveform/radio signal aesthetic
- **Acceptance Criteria:**
  - Sentiment Spectrum: full-width animated waveform chart (sentiment over time)
  - Insight cards: mini waveform decoration, expandable summary, action item checklist, decisions, risks
  - Action Tracker: floating side panel with pending/overdue/completed counts
  - Sentiment filter, customer filter, date range
  - Action item checkbox toggles status via API

#### F7: Ticket Warroom
- Dual-mode: Constellation (3D) + Warroom Table (2D)
- **Acceptance Criteria:**
  - Constellation: tickets as 3D stars (X=severity, Y=age, Z=status), SLA-breaching stars pulse red
  - Warroom Table: premium table with severity ribbons, live SLA countdowns (ticking per second), AI TRIAGED row shimmer
  - Ticket Detail Drawer: slides from right with AI triage, diagnostics, escalation summary, similar tickets (RAG)
  - Toggle between Constellation and Table views

#### F8: Analytics Lab
- Interactive data exploration with cross-filtering charts
- **Acceptance Criteria:**
  - Health Heatmap: calendar heatmap (customers × days)
  - Ticket Velocity: stacked area chart by severity
  - Sentiment River: stream graph
  - Agent Throughput: radial bar chart
  - Cross-filtering: selecting data in any chart highlights related data in all others
  - Report list + "Generate Report" modal (weekly/monthly/QBR)

#### F9: Real-Time WebSocket System
- **Acceptance Criteria:**
  - WebSocket maintained across page navigation
  - Events: agent_status, event_processed, new_alert, health_update, ticket_triaged, insight_ready
  - Toast notifications with particle trail animation for critical alerts
  - Dashboard components update in-place

#### F10: Navigation System (Orbital + Command Palette)
- **Acceptance Criteria:**
  - Orbital Nav: curved arc at bottom-center, 7 items, active item centered + enlarged
  - Command Palette: Cmd+K opens fuzzy search across Pages, Customers, Tickets, Agents, Actions
  - Breadcrumb Trail: floating at top-left with animated connecting dots
  - No sidebar anywhere in the application

#### F11: Seed Data System
- **Acceptance Criteria:**
  - 10 customers, 50+ tickets, 100+ insights, 30 days health history, agent logs, alerts, action items
  - Single CLI command: `python -m app.utils.seed`

### 2.2 Post-MVP Features (Phase 2)

| Feature | Description |
|---------|-------------|
| Slack Integration | Risk alerts to channels, @cs-bot commands, action item reminders |
| Jira Webhooks | Real-time ticket sync, auto-create, bi-directional status |
| Fathom Automation | Playwright-based recording extraction, transcript pipeline |
| Advanced RAG | Multi-turn queries, cross-customer patterns, resolution engine |
| Email Drafts | Auto-generate customer-facing emails from insights |

---

## 3. Non-Functional Requirements

### 3.1 Performance
- Dashboard initial load (with 3D): < 4 seconds
- Dashboard initial load (2D fallback): < 2 seconds
- API response times: < 500ms (CRUD), < 5s (AI-powered)
- WebSocket latency: < 100ms
- 3D scenes: 60fps on M1 MacBook / RTX 2060 equivalent
- Three.js bundle: lazy-loaded, code-split, NOT in main bundle
- Support 50 concurrent users

### 3.2 Security
- JWT auth (access 15min + refresh 7d)
- bcrypt passwords, RBAC on all endpoints
- CORS restricted, Pydantic validation, parameterized queries
- Rate limiting on auth endpoints

### 3.3 Design Requirements
- **Theme:** Dark mode only — "Deep Ocean Bioluminescence"
- **Background:** Void black (#020408) with animated nebula gradient mesh, NOT navy
- **Accents:** Two-tone — electric teal (#00F5D4) + rich violet (#8B5CF6)
- **Typography:** Space Grotesk (display), IBM Plex Mono (data), Inter (body)
- **Surfaces:** Frosted Depth — three opacity levels (near 0.65, mid 0.45, far 0.25) with backdrop-blur(20px)
- **Navigation:** Orbital arc at bottom-center, no sidebar. Cmd+K palette.
- **3D Elements:** Neural Sphere, Health Terrain, Floating Orbs, Data Flow Rivers, Ticket Constellation
- **Progressive Enhancement:** All 3D has 2D fallbacks. Respects prefers-reduced-motion.
- **Responsive:** Full 3D > 1440px, simplified 3D 1024-1440, premium 2D < 1024, mobile tab bar < 768

### 3.4 Accessibility
- Reduce Motion toggle in Settings
- prefers-reduced-motion media query respected (3D → 2D)
- All statuses use shape + icon + color (never color alone)
- Keyboard navigation for all 3D scenes
- Screen reader labels on all canvas elements

---

## 4. Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React 18 + Vite | |
| Styling | Tailwind CSS + custom CSS | Void/glow effects |
| State | Zustand | |
| Routing | React Router v6 | |
| HTTP | Axios | |
| **3D** | Three.js + @react-three/fiber + drei | Neural sphere, terrain, orbs |
| **Animation** | Framer Motion + GSAP | Page transitions, scroll, 3D camera |
| **Charts** | Recharts + D3 | Recharts (simple), D3 (heatmap, river, radial) |
| Interactions | @dnd-kit, fuse.js | Drag-drop, fuzzy search |
| Backend | FastAPI | |
| Database | PostgreSQL 16 | |
| Vector DB | ChromaDB | RAG |
| ORM | SQLAlchemy 2.0 + Alembic | |
| Auth | python-jose (JWT) | |
| Task Queue | Celery + Redis | |
| LLM | Claude API (Sonnet 4.5) | |
| Automation | Playwright (Python) | |
| Testing | Pytest + Playwright | |

---

## 5. System Architecture

### 5.1 The 10 Agents

| # | Agent | Lane | Trigger | Output |
|---|-------|------|---------|--------|
| 1 | CS Orchestrator | Control | All events | Routes to correct agent |
| 2 | Customer Memory Agent | Control | Read/Write from all | Structured customer profile |
| 3 | Call Intelligence Agent | Value | zoom_call_completed | Summary, action items, sentiment |
| 4 | Health Monitoring Agent | Value | daily_health_check | Scores, risk flags, alerts |
| 5 | QBR/Value Narrative | Value | renewal_90_days | QBR draft, value narrative |
| 6 | Ticket Triage Agent | Run/Support | jira_ticket_created | Category, severity, action |
| 7 | Troubleshooting Agent | Run/Support | support_bundle_uploaded | Root cause, evidence |
| 8 | Escalation Summary | Run/Support | ticket_escalated | Technical summary, repro steps |
| 9 | SOW & Prerequisite | Delivery | new_enterprise_customer | Pre-deployment checklist |
| 10 | Deployment Intelligence | Delivery | deployment_started | Known issues, config guidance |

### 5.2 Event-Driven Flow
```
Event → Orchestrator → Customer Memory (read) → Target Agent → Execute (Claude API via Celery) → Output → Customer Memory (update) → WebSocket broadcast → Dashboard update
```

---

## 6. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Pre-meeting prep time | 30-60 min → < 5 min | User survey |
| Ticket triage time | 15 min → < 2 min | Agent log timestamps |
| At-risk detection | 2 weeks earlier | Health alert timing |
| Call insight extraction | 100% of calls | Insight vs call count |
| QBR preparation | 2 days → 2 hours | User survey |
| Action item completion | > 80% rate | Status tracking |
| Stakeholder "wow" factor | Executive buy-in on first demo | Demo feedback |

---

## 7. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| 3D performance on low-end devices | Progressive enhancement — 2D fallbacks always work, 3D lazy-loaded |
| Three.js bundle size | Code-split into separate chunks, lazy-load on demand |
| Fathom lacks stable API | Playwright automation primary, manual upload fallback |
| Claude API cost scaling | Token tracking, batch processing, caching |
| Jira webhook reliability | Periodic polling fallback, retry logic |
| Agent hallucination | Confidence scores, human-in-the-loop for low confidence |
| Data privacy | RBAC, audit logging, no PII in embeddings |

---

## 8. Development Phases

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Phase 1-2 | Week 1-2 | Project setup, DB, Auth |
| Phase 3-4 | Week 3-4 | Customer CRUD, Core services, RAG |
| Phase 5-7 | Week 5-7 | Agent framework, all 10 agents, event system, WebSocket |
| Phase 8-9 | Week 8-9 | Frontend design system, Orbital Nav, Login, Dashboard (2D) |
| Phase 10 | Week 10 | Dashboard 3D upgrade (Neural Sphere, Orbs, Terrain, Rivers) |
| Phase 11-13 | Week 11-13 | Customer pages, Agent Nexus, Insights, Tickets |
| Phase 14 | Week 14 | Analytics Lab with cross-filtering |
| Phase 15-16 | Week 15-16 | Seed data, polish, animations, E2E tests, performance |

---

## 9. Stakeholders

| Person | Role | Interest |
|--------|------|----------|
| Kazi Sir | VP/Director | ROI, capability, team impact, visual impression |
| Ariza Zehra | AI Hub Lead | Technical feasibility, capacity |
| Vignesh / Chaitanya | CS Engineers | Daily usability, workflows |
| Priyank Tailang | QA | Testing, reliability |
| Ayushmaan Singh Naruka | Developer | Architecture, implementation |
| Divyam Garg | Developer | Co-development support |
