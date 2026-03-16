# Master Prompt — CS Control Plane Agentic Rebuild

> Paste this into a new Claude Code chat to continue the rebuild from where we left off.

---

## Context

You are continuing work on the **HivePro CS Control Plane** — an AI-powered Customer Success platform that orchestrates specialized agents to automate CS workflows.

**Read these files FIRST before doing anything:**
1. `CLAUDE.md` — Project rules, tech stack, architecture, coding standards
2. `REBUILD_PLAN.md` — The full rebuild plan (2500+ lines) with 9 phases, agent identities, file inventory, and detailed specs
3. `REFERENCE_ARCHITECTURE.md` — Reference architecture from an agentic simulation repo we're modeling after

## What's Already Done

### Phase 0: Fathom Integration (COMPLETE)
Real Fathom API integration is fully implemented:
- `backend/app/config.py` — Updated with `FATHOM_API_KEY`, `FATHOM_API_BASE_URL`, `FATHOM_WEBHOOK_SECRET`
- `backend/app/services/fathom_service.py` — Complete rewrite from mock to real httpx-based API client (~230 lines). Supports: `list_meetings()`, `list_all_meetings()` (with cursor pagination), `get_transcript()`, `get_summary()`, `create_webhook()`, `delete_webhook()`, `list_teams()`, `list_team_members()`, plus helper methods (`build_flat_transcript()`, `extract_participants()`, `estimate_duration_minutes()`)
- `backend/app/routers/webhooks.py` — NEW. `POST /api/webhooks/fathom` receives Fathom webhook POSTs, verifies HMAC-SHA256 signatures, extracts meeting data, pushes `fathom_recording_ready` events into the orchestrator pipeline
- `backend/app/routers/insights.py` — `POST /insights/sync-fathom` rewritten to actually call Fathom API, fetch meetings with transcripts, deduplicate by `fathom_recording_id`, and push new ones through the event pipeline
- `backend/app/main.py` — Webhooks router registered, Fathom status in startup log
- `.env.example` and `.env.production.example` — Updated with Fathom fields

## What's Next — Phase A: Documentation Update

**This is the current phase.** Before writing any implementation code for the rebuild, we need to update all documentation in `/docs/` to match the new agentic architecture.

### Phase A deliverables (read REBUILD_PLAN.md Section 7 for full details):

1. **Rewrite `docs/PRD.md`** (~400 lines) — Updated features, user stories, and acceptance criteria for:
   - 4-tier agent hierarchy (Orchestrator → Lane Leads → Specialists → Foundation)
   - Multi-round pipeline execution (perceive → retrieve → think → act → reflect → quality_gate → finalize)
   - 3-tier memory system (working + episodic + semantic)
   - 12+ agent tools
   - 9+ pluggable traits with lifecycle hooks
   - Inter-agent message board with delegation chains
   - Reflection engine with tier-appropriate depth
   - Full observability via structured execution traces
   - Complete frontend redesign (8 new pages/panels)

2. **Rewrite `docs/WIREFRAMES.md`** (~600 lines) — New page designs, panel layouts, and component specs for:
   - Agent Hierarchy View (4-tier tree with live delegation flow)
   - Pipeline Execution Page (real-time stages per agent)
   - Message Board Page (inter-agent communication feed)
   - Memory Inspector (browse episodic memories, knowledge pools)
   - Execution Trace Viewer (drill into any agent run)
   - Agent Profile Cards (personality, traits, tools per tier)
   - Workflow Designer/Viewer (event flow through hierarchy)
   - Live Dashboard (real-time activity stream)

3. **Rewrite `docs/API_CONTRACT.md`** (~500 lines) — New endpoints + updated schemas:
   - Pipeline execution traces API
   - Message board API
   - Memory inspector API
   - Agent hierarchy API
   - Webhook management API
   - Updated existing endpoints

4. **Rewrite `docs/DATABASE_SCHEMA.md`** (~300 lines) — New tables + schemas:
   - `agent_execution_rounds` table
   - `agent_messages` table
   - YAML config schemas (org_structure, agent_profiles, pipeline, workflows)
   - Updated ChromaDB collections (episodic_memory, shared_knowledge)

5. **Update `CLAUDE.md`** (~200 lines modified) — Updated project structure, architecture rules, coding standards for the new build

### Key references for writing docs:
- **REBUILD_PLAN.md** — Sections 1-5 for the big picture, Sections 8-14 for detailed phase specs
- **Agent identities table** — 13 named agents at the top of REBUILD_PLAN.md
- **4-tier hierarchy diagram** — Section 4.1 of REBUILD_PLAN.md
- **Pipeline stages** — Section 4.5 (different configs per tier)
- **Memory system** — Section 4.6 (working + episodic + semantic)
- **Message board** — Section 4.7 (5 message types with direction)
- **Current docs** — Read existing `/docs/*.md` files to understand the current format and coverage

## Phase Order After Docs

After Phase A, the implementation order is:
- **Phase B: Foundation** (3-4 days) — YAML configs, profile loader, tool registry, Claude tool_use, pipeline engine, execution logger
- **Phase C: Memory** (1-2 days) — 3-tier memory manager, ChromaDB collections
- **Phase D: Traits + Reflection** (1-2 days) — Trait registry, 9+ CS traits, reflection engine
- **Phase E: Message Board** (2-3 days) — Agent messages DB table, delegation chains, workflow configs
- **Phase F: Agents** (3-4 days) — Implement Orchestrator (Tier 1), 3 Lane Leads (Tier 2), migrate 8 Specialists (Tier 3), upgrade Memory Agent (Tier 4)
- **Phase G: Frontend** (5-7 days) — Complete redesign with 8 new pages/panels
- **Phase H: Integration** (1-2 days) — Celery updates, WebSocket events, feature flags, seed data

## Agent Team (for reference in all docs)

| ID | Name | Tier | Role |
|---|---|---|---|
| `cso_orchestrator` | Naveen Kapoor | 1 | CS Manager |
| `support_lead` | Rachel Torres | 2 | Support Operations Lead |
| `value_lead` | Damon Reeves | 2 | Value & Insights Lead |
| `delivery_lead` | Priya Mehta | 2 | Delivery Operations Lead |
| `triage_agent` | Kai Nakamura | 3 | Ticket Triage Specialist |
| `troubleshooter_agent` | Leo Petrov | 3 | Troubleshooting Engineer |
| `escalation_agent` | Maya Santiago | 3 | Escalation Manager |
| `health_monitor_agent` | Dr. Aisha Okafor | 3 | Customer Health Analyst |
| `call_intel_agent` | Jordan Ellis | 3 | Call Intelligence Analyst |
| `qbr_agent` | Sofia Marquez | 3 | QBR & Review Specialist |
| `sow_agent` | Ethan Brooks | 3 | Scope & SOW Specialist |
| `deployment_intel_agent` | Zara Kim | 3 | Deployment Intelligence Analyst |
| `customer_memory` | Atlas | 4 | Customer Memory Manager |

## Instructions

1. Read `CLAUDE.md`, `REBUILD_PLAN.md`, and all existing `/docs/*.md` files
2. Start with Phase A: Documentation Update
3. Work through each doc file one at a time (PRD → WIREFRAMES → API_CONTRACT → DATABASE_SCHEMA → CLAUDE.md)
4. Use REBUILD_PLAN.md as the source of truth for all technical details
5. Keep the writing style clear and practical — these docs are the blueprint for implementation
6. After Phase A is complete, proceed to Phase B: Foundation
7. For each phase, read the corresponding section in REBUILD_PLAN.md for the detailed spec before implementing

**Start by reading the files listed above, then begin Phase A.**
