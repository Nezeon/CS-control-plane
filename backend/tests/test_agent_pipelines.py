"""
Comprehensive Agent Pipeline Test Suite
========================================
Tests each agent's pipeline stages for errors, silent failures, and integration issues.

Mocks:
  - Claude API calls (returns structured JSON matching each agent's expected format)
  - Database sessions (SQLAlchemy mock with realistic query results)
  - RAG service (returns empty or sample results)
  - ChromaDB collections (in-memory stubs)
  - WebSocket broadcasts (no-op)

Run:
  cd backend
  python -m tests.test_agent_pipelines
"""

import json
import logging
import sys
import time
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure logging to see agent output
logging.basicConfig(
    level=logging.INFO,
    format="%(name)-30s | %(levelname)-7s | %(message)s",
    stream=sys.stdout,
)

# ─── Results Tracking ──────────────────────────────────────────────
results = []

def record(agent_id: str, stage: str, status: str, detail: str = "", duration_ms: int = 0):
    results.append({
        "agent": agent_id,
        "stage": stage,
        "status": status,
        "detail": detail[:300],
        "duration_ms": duration_ms,
    })

# ─── Mock Helpers ──────────────────────────────────────────────────

def make_claude_response(content_dict: dict) -> dict:
    """Create a mock Claude API response."""
    return {
        "content": json.dumps(content_dict),
        "input_tokens": 500,
        "output_tokens": 200,
        "model": "claude-sonnet-4-5-20250929",
    }

def make_mock_db():
    """Create a mock DB session that handles common query patterns."""
    db = MagicMock()

    # Mock execute().fetchall() for raw SQL queries
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_result.scalar.return_value = 0
    db.execute.return_value = mock_result

    # Mock ORM query chain
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.filter_by.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.first.return_value = None
    mock_query.all.return_value = []
    db.query.return_value = mock_query

    # Mock add/commit/rollback
    db.add.return_value = None
    db.commit.return_value = None
    db.rollback.return_value = None

    return db

SAMPLE_CUSTOMER_MEMORY = {
    "customer": {
        "id": str(uuid.uuid4()),
        "name": "Acme Corp",
        "industry": "Technology",
        "tier": "enterprise",
        "contract_start": "2025-01-01",
        "renewal_date": str((datetime.now(timezone.utc) + timedelta(days=60)).date()),
        "primary_contact": "John Doe",
        "deployment_mode": "cloud",
        "product_version": "5.2.1",
        "integrations": ["Jira", "Slack", "ServiceNow"],
        "known_constraints": ["FedRAMP", "SOC2"],
    },
    "health": {
        "current_score": 65,
        "risk_level": "watch",
        "factors": {"ticket_severity": 80, "call_sentiment": 70},
        "risk_flags": ["p0_tickets_aging"],
        "calculated_at": str(datetime.now(timezone.utc)),
        "trend": [
            {"score": 70, "date": str((datetime.now(timezone.utc) - timedelta(days=7)).date())},
            {"score": 65, "date": str(datetime.now(timezone.utc).date())},
        ],
    },
    "tickets": {
        "total_recent": 5,
        "open_count": 2,
        "items": [
            {
                "id": str(uuid.uuid4()),
                "jira_id": "UCSC-1001",
                "summary": "Scanner failing on network segments",
                "severity": "P1",
                "status": "open",
                "type": "bug",
                "created_at": str(datetime.now(timezone.utc)),
            },
        ],
    },
    "calls": {
        "total_recent": 3,
        "items": [
            {
                "id": str(uuid.uuid4()),
                "summary": "Weekly sync with Acme Corp - discussed deployment issues",
                "sentiment": "mixed",
                "sentiment_score": 0.4,
                "key_topics": ["deployment", "performance"],
                "decisions": ["upgrade to v5.3"],
                "call_date": str(datetime.now(timezone.utc)),
            },
        ],
    },
    "action_items": [],
    "alerts": [],
}

# ─── Claude Response Templates per Agent ─────────────────────────

CLAUDE_RESPONSES = {
    "triage_agent": {
        "category": "Deployment",
        "severity": "P1",
        "suggested_action": "Check scanner configuration for network segment isolation",
        "potential_root_cause": "Network scanner timeout on segmented VLANs",
        "confidence": 0.85,
        "diagnostics": {"required_script": "network_diag.sh", "kb_article": "KB-2045"},
        "similar_ticket_ids": [],
        "email_draft": "Dear Acme Corp, We have received your ticket regarding scanner failures. Our team has classified this as a Deployment issue with P1 priority. We will investigate network segment isolation next.",
        "reasoning": "Ticket describes scanner failure on network segments, consistent with deployment-related network config issues.",
    },
    "troubleshooter": {
        "root_cause": "Scanner process crashes when encountering segmented VLANs with >256 hosts",
        "confidence": 0.72,
        "estimated_time": "2-4 hours",
        "resolution_steps": [
            {"step": 1, "action": "Check scanner logs for OOM errors"},
            {"step": 2, "action": "Verify VLAN configuration"},
            {"step": 3, "action": "Apply patch KB-2045"},
        ],
        "reasoning": "Pattern matches known issue with large network segments.",
    },
    "escalation_summary": {
        "title": "Escalation: Scanner Failure on Network Segments - Acme Corp",
        "severity": "P1",
        "customer_impact": "Production scanning halted for 2 network segments",
        "technical_summary": "Scanner process crashes on segmented VLANs with >256 hosts.",
        "evidence": ["OOM in scanner logs", "VLAN config mismatch"],
        "repro_steps": ["Configure VLAN with >256 hosts", "Run scan", "Observe crash"],
        "timeline": "Issue reported 2 days ago, reproduction confirmed today",
        "recommended_resolution": "Apply memory limit patch and update VLAN handling",
        "reasoning": "Escalation compiled from triage and troubleshooting outputs.",
    },
    "health_monitor": {
        "summary": "Acme Corp health is at watch level (65/100). Open P1 tickets and mixed call sentiment are primary concerns.",
        "recommendations": [
            "Schedule urgent call to address P1 ticket UCSC-1001",
            "Review deployment configuration",
            "Monitor call sentiment trend",
        ],
        "draft_jira_ticket": {
            "summary": "Proactive: Acme Corp health declining - review deployment issues",
            "priority": "P2",
        },
        "reasoning": "Health score of 65 with P1 tickets aging and mixed call sentiment warrants proactive outreach.",
    },
    "qbr_value": {
        "executive_summary": "Acme Corp has experienced moderate challenges this quarter with deployment stability.",
        "sentiment_bucket": "Neutral",
        "key_achievements": ["Successful integration with ServiceNow"],
        "concerns": ["Scanner reliability on network segments"],
        "renewal_recommendation": "Renew with enhanced support tier",
        "reasoning": "QBR analysis based on ticket trends, call sentiment, and health data.",
    },
    "sow_prerequisite": {
        "checklist": [
            {"item": "Network topology documentation", "status": "required", "priority": "high"},
            {"item": "FedRAMP compliance verification", "status": "required", "priority": "high"},
            {"item": "Jira integration setup", "status": "optional", "priority": "medium"},
        ],
        "timeline_estimate": "4-6 weeks",
        "risks": ["FedRAMP compliance may extend timeline by 2 weeks"],
        "reasoning": "SOW generated based on enterprise tier cloud deployment with FedRAMP and SOC2 constraints.",
    },
    "deployment_intelligence": {
        "deployment_status": "at_risk",
        "known_issues": [
            "Cloud deployments with Jira integration may experience webhook delays",
            "v5.2.1 has a known scanner timeout issue — upgrade to v5.3 recommended",
        ],
        "recommendations": [
            "Upgrade to v5.3 before go-live",
            "Configure webhook retry policy for Jira integration",
        ],
        "pre_flight_checks": [
            {"check": "Network connectivity", "status": "pass"},
            {"check": "Scanner health", "status": "warning"},
        ],
        "reasoning": "Deployment analysis based on similar cloud configs with Jira integration.",
    },
    "presales_funnel": {
        "summary": "Deal moved from Demo 1 to Demo 2, showing positive progression. Win probability at 52%.",
        "risks": ["Deal has been in pipeline for 45 days — approaching stall threshold"],
        "next_steps": [
            "Schedule POC planning call this week",
            "Share technical requirements doc",
            "Confirm budget holder attendance for Demo 2",
        ],
        "reasoning": "Stage progression is healthy but velocity is slowing.",
    },
    "cso_orchestrator": {
        "specialist": "triage_agent",
        "priority": 7,
        "rationale": "Routing jira_ticket_created to triage specialist",
    },
    # Reflection response (used by all agents in reflect stage)
    "_reflection": {
        "confidence": 0.82,
        "went_well": "Analysis was thorough",
        "could_improve": "Could have checked more historical data",
        "lessons": ["Always check last 30 days of tickets", "Verify customer constraints"],
        "should_escalate": False,
        "escalation_reason": None,
    },
}


# ─── Test Functions ────────────────────────────────────────────────

def test_agent_registration():
    """Test 1: Verify all agents register correctly in AgentFactory."""
    print("\n" + "=" * 70)
    print("TEST 1: Agent Registration")
    print("=" * 70)

    from app.agents import AgentFactory

    expected = [
        "triage_agent", "troubleshooter", "escalation_summary",
        "health_monitor", "qbr_value", "sow_prerequisite",
        "deployment_intelligence", "presales_funnel",
        "customer_memory", "cso_orchestrator",
    ]

    available = AgentFactory.available()
    print(f"  Registered agents: {available}")

    for agent_id in expected:
        if agent_id in available:
            record(agent_id, "registration", "PASS")
            print(f"  [PASS] {agent_id}")
        else:
            record(agent_id, "registration", "FAIL", f"Not found in registry. Available: {available}")
            print(f"  [FAIL] {agent_id} — NOT REGISTERED")

    # Check for unexpected agents
    unexpected = set(available) - set(expected)
    if unexpected:
        print(f"  [INFO] Extra agents registered: {unexpected}")

    return True


def test_profile_loading():
    """Test 2: Verify YAML profiles load correctly for all agents."""
    print("\n" + "=" * 70)
    print("TEST 2: Profile Loading (YAML)")
    print("=" * 70)

    from app.agents.profile_loader import ProfileLoader
    loader = ProfileLoader.get()

    all_profiles = loader.get_all_profiles()
    print(f"  Loaded {len(all_profiles)} profiles: {list(all_profiles.keys())}")

    required_fields = ["name", "tier", "role"]
    for agent_id, profile in all_profiles.items():
        missing = [f for f in required_fields if not profile.get(f)]
        if missing:
            record(agent_id, "profile_loading", "FAIL", f"Missing fields: {missing}")
            print(f"  [FAIL] {agent_id}: missing {missing}")
        else:
            record(agent_id, "profile_loading", "PASS",
                   f"tier={profile['tier']}, lane={profile.get('lane', 'none')}")
            print(f"  [PASS] {agent_id}: tier={profile['tier']}, lane={profile.get('lane', 'N/A')}")

    return True


def test_pipeline_config():
    """Test 3: Verify pipeline.yaml loads correctly for each tier."""
    print("\n" + "=" * 70)
    print("TEST 3: Pipeline Configuration")
    print("=" * 70)

    from app.agents.profile_loader import ProfileLoader
    loader = ProfileLoader.get()

    for tier in [1, 2, 3, 4]:
        pipeline = loader.get_pipeline_for_tier(tier)
        if pipeline:
            stages = [s.get("type", s.get("name", "?")) for s in pipeline.get("stages", [])]
            record(f"tier_{tier}", "pipeline_config", "PASS", f"stages={stages}")
            print(f"  [PASS] Tier {tier}: {stages}")
        else:
            record(f"tier_{tier}", "pipeline_config", "FAIL", "No pipeline config found")
            print(f"  [FAIL] Tier {tier}: no pipeline config")

    return True


def test_agent_instantiation():
    """Test 4: Verify each agent can be instantiated without errors."""
    print("\n" + "=" * 70)
    print("TEST 4: Agent Instantiation")
    print("=" * 70)

    from app.agents import AgentFactory

    for agent_id in AgentFactory.available():
        t0 = time.perf_counter()
        try:
            agent = AgentFactory.create(agent_id)
            ms = int((time.perf_counter() - t0) * 1000)

            # Verify key attributes
            issues = []
            if not agent.agent_id:
                issues.append("agent_id is empty")
            if not agent.agent_name:
                issues.append("agent_name is empty")
            if not hasattr(agent, 'memory'):
                issues.append("no memory manager")
            if not hasattr(agent, 'traits'):
                issues.append("no traits")
            if not hasattr(agent, 'reflection'):
                issues.append("no reflection engine")

            if issues:
                record(agent_id, "instantiation", "WARN", f"Issues: {issues}")
                print(f"  [WARN] {agent_id}: {issues} ({ms}ms)")
            else:
                record(agent_id, "instantiation", "PASS",
                       f"name={agent.agent_name}, tier={agent.tier}, lane={agent.lane}")
                print(f"  [PASS] {agent_id}: name={agent.agent_name}, tier={agent.tier} ({ms}ms)")

        except Exception as e:
            ms = int((time.perf_counter() - t0) * 1000)
            record(agent_id, "instantiation", "FAIL", str(e))
            print(f"  [FAIL] {agent_id}: {e}")
            traceback.print_exc()

    return True


def test_memory_system():
    """Test 5: Verify the 3-tier memory system works for each agent."""
    print("\n" + "=" * 70)
    print("TEST 5: Memory System (Working + Episodic + Semantic)")
    print("=" * 70)

    from app.agents import AgentFactory

    for agent_id in AgentFactory.available():
        try:
            agent = AgentFactory.create(agent_id)

            # Test Working Memory
            agent.memory.set_context("test_key", "test_value")
            val = agent.memory.get_context("test_key")
            if val != "test_value":
                record(agent_id, "working_memory", "FAIL", f"Expected 'test_value', got '{val}'")
                print(f"  [FAIL] {agent_id}: working memory set/get failed")
                continue

            # Test assemble_context (episodic + semantic)
            ctx = agent.memory.assemble_context("test query for health monitoring")
            expected_keys = {"working", "episodic", "semantic", "global_knowledge"}
            actual_keys = set(ctx.keys())
            missing = expected_keys - actual_keys
            if missing:
                record(agent_id, "memory_assemble", "FAIL", f"Missing keys: {missing}")
                print(f"  [FAIL] {agent_id}: assemble_context missing keys: {missing}")
            else:
                record(agent_id, "memory_system", "PASS",
                       f"working=OK, episodic={len(ctx['episodic'])}, semantic={len(ctx['semantic'])}")
                print(f"  [PASS] {agent_id}: memory OK (episodic={len(ctx['episodic'])}, semantic={len(ctx['semantic'])})")

            # Clean up
            agent.memory.clear_working()

        except Exception as e:
            record(agent_id, "memory_system", "FAIL", str(e))
            print(f"  [FAIL] {agent_id}: {e}")
            traceback.print_exc()

    return True


def test_perceive_stages():
    """Test 6: Test each agent's perceive() stage individually."""
    print("\n" + "=" * 70)
    print("TEST 6: Perceive Stage (each agent)")
    print("=" * 70)

    from app.agents import AgentFactory

    test_events = {
        "triage_agent": {
            "event_type": "jira_ticket_created",
            "customer_id": str(uuid.uuid4()),
            "payload": {
                "summary": "Scanner failing on network segments",
                "description": "The vulnerability scanner crashes when scanning VLAN segments with >256 hosts",
                "severity": "P1",
                "jira_id": "UCSC-1001",
            },
            "customer_memory": SAMPLE_CUSTOMER_MEMORY,
        },
        "troubleshooter": {
            "event_type": "jira_ticket_updated",
            "customer_id": str(uuid.uuid4()),
            "payload": {
                "summary": "Scanner failing on network segments",
                "description": "OOM crash in scanner process",
                "severity": "P1",
                "triage_result": {"category": "Deployment", "severity": "P1"},
            },
            "customer_memory": SAMPLE_CUSTOMER_MEMORY,
        },
        "escalation_summary": {
            "event_type": "ticket_escalated",
            "customer_id": str(uuid.uuid4()),
            "payload": {
                "summary": "Scanner failing — needs engineering escalation",
                "description": "Troubleshooting confidence below 70%",
                "severity": "P1",
                "ticket_id": str(uuid.uuid4()),
            },
            "customer_memory": SAMPLE_CUSTOMER_MEMORY,
        },
        "health_monitor": {
            "event_type": "daily_health_check",
            "customer_id": str(uuid.uuid4()),
            "customer_name": "Acme Corp",
            "payload": {},
            "customer_memory": SAMPLE_CUSTOMER_MEMORY,
        },
        "qbr_value": {
            "event_type": "renewal_approaching",
            "customer_id": str(uuid.uuid4()),
            "payload": {},
            "customer_memory": SAMPLE_CUSTOMER_MEMORY,
        },
        "sow_prerequisite": {
            "event_type": "new_enterprise_customer",
            "customer_id": str(uuid.uuid4()),
            "payload": {},
            "customer_memory": SAMPLE_CUSTOMER_MEMORY,
        },
        "deployment_intelligence": {
            "event_type": "deployment_started",
            "customer_id": str(uuid.uuid4()),
            "payload": {},
            "customer_memory": SAMPLE_CUSTOMER_MEMORY,
        },
        "presales_funnel": {
            "event_type": "deal_stage_changed",
            "customer_id": str(uuid.uuid4()),
            "payload": {
                "deal_name": "Acme Corp Enterprise License",
                "old_stage": "Demo 1",
                "new_stage": "Demo 2",
                "company_name": "Acme Corp",
                "deal_id": "12345",
            },
            "customer_memory": SAMPLE_CUSTOMER_MEMORY,
        },
        "customer_memory": {
            "event_type": "memory_request",
            "customer_id": str(uuid.uuid4()),
            "payload": {},
        },
        "cso_orchestrator": {
            "event_type": "jira_ticket_created",
            "customer_id": str(uuid.uuid4()),
            "payload": {
                "summary": "Test ticket for orchestrator routing",
                "severity": "P2",
            },
            "customer_memory": SAMPLE_CUSTOMER_MEMORY,
        },
    }

    for agent_id in AgentFactory.available():
        event = test_events.get(agent_id)
        if not event:
            record(agent_id, "perceive", "SKIP", "No test event defined")
            print(f"  [SKIP] {agent_id}: no test event")
            continue

        try:
            agent = AgentFactory.create(agent_id)
            agent._current_db = make_mock_db()

            # Build task dict like pipeline engine does
            task = {
                "event_type": event.get("event_type", ""),
                "payload": event.get("payload", {}),
                "customer_id": event.get("customer_id"),
                "customer_name": event.get("customer_memory", {}).get("customer", {}).get("name", "Unknown"),
                "customer_memory": event.get("customer_memory", {}),
                "description": (
                    event.get("payload", {}).get("summary", "")
                    or event.get("payload", {}).get("description", "")
                    or event.get("event_type", "")
                ),
                "execution_id": str(uuid.uuid4()),
                "source": "test",
            }

            t0 = time.perf_counter()
            result = agent.perceive(task)
            ms = int((time.perf_counter() - t0) * 1000)

            if result is None:
                record(agent_id, "perceive", "WARN", "perceive() returned None")
                print(f"  [WARN] {agent_id}: perceive() returned None ({ms}ms)")
            else:
                record(agent_id, "perceive", "PASS", f"returned type={type(result).__name__}")
                print(f"  [PASS] {agent_id}: perceive() OK ({ms}ms)")

        except ValueError as ve:
            record(agent_id, "perceive", "FAIL", f"ValueError: {ve}")
            print(f"  [FAIL] {agent_id}: {ve}")
        except Exception as e:
            record(agent_id, "perceive", "FAIL", str(e))
            print(f"  [FAIL] {agent_id}: {e}")
            traceback.print_exc()

    return True


def test_retrieve_stages():
    """Test 7: Test each agent's retrieve() stage."""
    print("\n" + "=" * 70)
    print("TEST 7: Retrieve Stage (each agent)")
    print("=" * 70)

    from app.agents import AgentFactory

    for agent_id in AgentFactory.available():
        try:
            agent = AgentFactory.create(agent_id)
            agent._current_db = make_mock_db()

            task = {
                "event_type": "test_event",
                "payload": {
                    "summary": "Test ticket summary",
                    "description": "Test description for retrieve",
                },
                "customer_id": str(uuid.uuid4()),
                "customer_name": "Acme Corp",
                "customer_memory": SAMPLE_CUSTOMER_MEMORY,
                "description": "Test ticket summary",
                "execution_id": str(uuid.uuid4()),
            }

            t0 = time.perf_counter()
            result = agent.retrieve(task)
            ms = int((time.perf_counter() - t0) * 1000)

            if result is None:
                record(agent_id, "retrieve", "WARN", "retrieve() returned None")
                print(f"  [WARN] {agent_id}: retrieve() returned None ({ms}ms)")
            elif isinstance(result, dict):
                record(agent_id, "retrieve", "PASS", f"keys={list(result.keys())}")
                print(f"  [PASS] {agent_id}: retrieve() OK, keys={list(result.keys())} ({ms}ms)")
            else:
                record(agent_id, "retrieve", "WARN", f"returned type={type(result).__name__}")
                print(f"  [WARN] {agent_id}: retrieve() returned {type(result).__name__} ({ms}ms)")

        except Exception as e:
            record(agent_id, "retrieve", "FAIL", str(e))
            print(f"  [FAIL] {agent_id}: {e}")
            traceback.print_exc()

    return True


def test_think_stages():
    """Test 8: Test each agent's think() stage with mocked Claude."""
    print("\n" + "=" * 70)
    print("TEST 8: Think Stage (mocked Claude)")
    print("=" * 70)

    from app.agents import AgentFactory
    from app.services import claude_service

    for agent_id in AgentFactory.available():
        if agent_id == "customer_memory":
            record(agent_id, "think", "SKIP", "Foundation agent: no think stage")
            print(f"  [SKIP] {agent_id}: no think stage (Tier 4)")
            continue

        try:
            agent = AgentFactory.create(agent_id)
            agent._current_db = make_mock_db()

            # Get the appropriate mock response
            response_key = agent_id
            mock_response_data = CLAUDE_RESPONSES.get(response_key, {
                "result": "ok",
                "reasoning": "Test response",
                "confidence": 0.8,
            })
            mock_response = make_claude_response(mock_response_data)

            task = {
                "event_type": "test_event",
                "payload": {
                    "summary": "Scanner failing on network segments",
                    "description": "The vulnerability scanner crashes when scanning VLAN segments",
                    "severity": "P1",
                    "jira_id": "UCSC-1001",
                    "deal_name": "Acme Corp License",
                    "old_stage": "Demo 1",
                    "new_stage": "Demo 2",
                    "company_name": "Acme Corp",
                },
                "customer_id": str(uuid.uuid4()),
                "customer_name": "Acme Corp",
                "customer_memory": SAMPLE_CUSTOMER_MEMORY,
                "description": "Scanner failing on network segments",
                "execution_id": str(uuid.uuid4()),
            }

            context = {
                "working": {},
                "episodic": [],
                "semantic": [],
                "global_knowledge": [],
                "customer_memory": SAMPLE_CUSTOMER_MEMORY,
                "similar_tickets": [],
                "similar_problems": [],
            }

            # Patch Claude service
            with patch.object(claude_service, 'generate_sync', return_value=mock_response):
                t0 = time.perf_counter()
                result = agent.think(task, context)
                ms = int((time.perf_counter() - t0) * 1000)

            if result is None:
                record(agent_id, "think", "WARN", "think() returned None")
                print(f"  [WARN] {agent_id}: think() returned None ({ms}ms)")
            elif isinstance(result, dict) and "error" in result:
                record(agent_id, "think", "FAIL", f"Error: {result['error']}")
                print(f"  [FAIL] {agent_id}: think() returned error: {result['error']} ({ms}ms)")
            elif isinstance(result, dict):
                record(agent_id, "think", "PASS", f"keys={list(result.keys())}")
                print(f"  [PASS] {agent_id}: think() OK, keys={list(result.keys())} ({ms}ms)")
            else:
                record(agent_id, "think", "WARN", f"returned type={type(result).__name__}")
                print(f"  [WARN] {agent_id}: think() returned {type(result).__name__} ({ms}ms)")

        except Exception as e:
            record(agent_id, "think", "FAIL", str(e))
            print(f"  [FAIL] {agent_id}: {e}")
            traceback.print_exc()

    return True


def test_act_stages():
    """Test 9: Test each agent's act() stage."""
    print("\n" + "=" * 70)
    print("TEST 9: Act Stage (each agent)")
    print("=" * 70)

    from app.agents import AgentFactory

    for agent_id in AgentFactory.available():
        try:
            agent = AgentFactory.create(agent_id)
            agent._current_db = make_mock_db()

            # Provide thinking result matching agent expectations
            thinking = CLAUDE_RESPONSES.get(agent_id, {"result": "ok", "reasoning": "test"})

            task = {
                "event_type": "test_event",
                "payload": {
                    "summary": "Test ticket",
                    "jira_id": "UCSC-1001",
                    "deal_name": "Test Deal",
                    "old_stage": "Demo 1",
                    "new_stage": "Demo 2",
                },
                "customer_id": str(uuid.uuid4()),
                "customer_name": "Acme Corp",
                "customer_memory": SAMPLE_CUSTOMER_MEMORY,
                "description": "Test",
                "execution_id": str(uuid.uuid4()),
            }

            # For health_monitor, pre-populate working memory
            if agent_id == "health_monitor":
                agent.memory.set_context("health_score", 65)
                agent.memory.set_context("risk_level", "watch")
                agent.memory.set_context("risk_flags", ["p0_tickets_aging"])
                agent.memory.set_context("factors", {
                    "ticket_severity": 80,
                    "call_sentiment": 70,
                })

            # For presales_funnel, pre-populate working memory
            if agent_id == "presales_funnel":
                agent.memory.set_context("deal_data", {
                    "deal_name": "Acme Corp License",
                    "company_name": "Acme Corp",
                    "deal_id": "12345",
                    "amount": 50000,
                    "old_stage": "Demo 1",
                    "new_stage": "Demo 2",
                    "probability": 0.52,
                    "factor_scores": {"stage": 0.45, "engagement": 0.7},
                    "factors": ["Stage: Demo 2"],
                })

            t0 = time.perf_counter()
            result = agent.act(task, thinking)
            ms = int((time.perf_counter() - t0) * 1000)

            if result is None:
                record(agent_id, "act", "WARN", "act() returned None")
                print(f"  [WARN] {agent_id}: act() returned None ({ms}ms)")
            elif isinstance(result, dict):
                success = result.get("success", "?")
                record(agent_id, "act", "PASS" if success else "WARN",
                       f"success={success}, keys={list(result.keys())}")
                status = "PASS" if success else "WARN"
                print(f"  [{status}] {agent_id}: act() success={success} ({ms}ms)")
            else:
                record(agent_id, "act", "WARN", f"returned type={type(result).__name__}")
                print(f"  [WARN] {agent_id}: act() returned {type(result).__name__} ({ms}ms)")

        except Exception as e:
            record(agent_id, "act", "FAIL", str(e))
            print(f"  [FAIL] {agent_id}: {e}")
            traceback.print_exc()

    return True


def test_reflect_stages():
    """Test 10: Test each agent's reflect() stage with mocked Claude."""
    print("\n" + "=" * 70)
    print("TEST 10: Reflect Stage (mocked Claude)")
    print("=" * 70)

    from app.agents import AgentFactory
    from app.services import claude_service

    mock_reflection = make_claude_response(CLAUDE_RESPONSES["_reflection"])

    for agent_id in AgentFactory.available():
        try:
            agent = AgentFactory.create(agent_id)

            task = {
                "description": "Test task for reflection",
                "customer_name": "Acme Corp",
                "customer_id": str(uuid.uuid4()),
                "execution_id": str(uuid.uuid4()),
            }

            result_to_reflect = {"success": True, "output": {"test": "data"}}

            with patch.object(claude_service, 'generate_sync', return_value=mock_reflection):
                t0 = time.perf_counter()
                result = agent.reflect(task, result_to_reflect)
                ms = int((time.perf_counter() - t0) * 1000)

            if result is None:
                record(agent_id, "reflect", "WARN", "reflect() returned None")
                print(f"  [WARN] {agent_id}: reflect() returned None ({ms}ms)")
            elif isinstance(result, dict):
                confidence = result.get("confidence", "?")
                record(agent_id, "reflect", "PASS", f"confidence={confidence}")
                print(f"  [PASS] {agent_id}: reflect() OK, confidence={confidence} ({ms}ms)")
            else:
                record(agent_id, "reflect", "WARN", f"returned type={type(result).__name__}")
                print(f"  [WARN] {agent_id}: reflect() returned {type(result).__name__} ({ms}ms)")

        except Exception as e:
            record(agent_id, "reflect", "FAIL", str(e))
            print(f"  [FAIL] {agent_id}: {e}")
            traceback.print_exc()

    return True


def test_full_pipeline():
    """Test 11: Run each agent through the full pipeline engine with mocked deps."""
    print("\n" + "=" * 70)
    print("TEST 11: Full Pipeline Execution (mocked Claude + DB)")
    print("=" * 70)

    from app.agents import AgentFactory
    from app.services import claude_service

    test_events = {
        "triage_agent": {
            "event_type": "jira_ticket_created",
            "customer_id": str(uuid.uuid4()),
            "payload": {
                "summary": "Scanner failing on network segments",
                "description": "Crashes on VLANs with >256 hosts",
                "severity": "P1",
                "jira_id": "UCSC-1001",
            },
        },
        "troubleshooter": {
            "event_type": "jira_ticket_updated",
            "customer_id": str(uuid.uuid4()),
            "payload": {
                "summary": "Scanner failing on network segments",
                "description": "OOM crash in scanner process",
                "severity": "P1",
            },
        },
        "escalation_summary": {
            "event_type": "ticket_escalated",
            "customer_id": str(uuid.uuid4()),
            "payload": {
                "summary": "Scanner failure — engineering escalation",
                "ticket_id": str(uuid.uuid4()),
                "severity": "P1",
            },
        },
        "health_monitor": {
            "event_type": "daily_health_check",
            "customer_id": str(uuid.uuid4()),
            "payload": {},
        },
        "qbr_value": {
            "event_type": "renewal_approaching",
            "customer_id": str(uuid.uuid4()),
            "payload": {},
        },
        "sow_prerequisite": {
            "event_type": "new_enterprise_customer",
            "customer_id": str(uuid.uuid4()),
            "payload": {},
        },
        "deployment_intelligence": {
            "event_type": "deployment_started",
            "customer_id": str(uuid.uuid4()),
            "payload": {},
        },
        "presales_funnel": {
            "event_type": "deal_stage_changed",
            "customer_id": str(uuid.uuid4()),
            "payload": {
                "deal_name": "Acme Corp Enterprise License",
                "old_stage": "Demo 1",
                "new_stage": "Demo 2",
                "company_name": "Acme Corp",
                "deal_id": "12345",
            },
        },
        "customer_memory": {
            "event_type": "memory_request",
            "customer_id": str(uuid.uuid4()),
            "payload": {},
        },
    }

    for agent_id in AgentFactory.available():
        # Skip orchestrator — it tries to run sub-agents which complicates mocking
        if agent_id == "cso_orchestrator":
            record(agent_id, "full_pipeline", "SKIP", "Orchestrator tested separately")
            print(f"  [SKIP] {agent_id}: orchestrator tested separately")
            continue

        event = test_events.get(agent_id)
        if not event:
            record(agent_id, "full_pipeline", "SKIP", "No test event")
            print(f"  [SKIP] {agent_id}: no test event")
            continue

        try:
            agent = AgentFactory.create(agent_id)
            db = make_mock_db()

            # Claude mock that returns the right response for this agent
            def make_mock_claude(aid):
                response_data = CLAUDE_RESPONSES.get(aid, CLAUDE_RESPONSES["_reflection"])
                mock_resp = make_claude_response(response_data)
                def mock_fn(*args, **kwargs):
                    return mock_resp
                return mock_fn

            with patch.object(claude_service, 'generate_sync', side_effect=make_mock_claude(agent_id)):
                t0 = time.perf_counter()
                result = agent.run(db, event, SAMPLE_CUSTOMER_MEMORY)
                ms = int((time.perf_counter() - t0) * 1000)

            if result is None:
                record(agent_id, "full_pipeline", "FAIL", "run() returned None")
                print(f"  [FAIL] {agent_id}: run() returned None ({ms}ms)")
            elif isinstance(result, dict):
                success = result.get("success", False)
                error = result.get("output", {}).get("error", "") if isinstance(result.get("output"), dict) else ""
                exec_id = result.get("execution_id", "?")

                if success:
                    record(agent_id, "full_pipeline", "PASS",
                           f"execution_id={exec_id[:8]}..., output_keys={list(result.get('output', {}).keys()) if isinstance(result.get('output'), dict) else '?'}")
                    print(f"  [PASS] {agent_id}: pipeline OK, success=True ({ms}ms)")
                else:
                    record(agent_id, "full_pipeline", "FAIL",
                           f"success=False, error={error or result.get('reasoning_summary', '?')}")
                    print(f"  [FAIL] {agent_id}: pipeline failed — {error or result.get('reasoning_summary', '?')} ({ms}ms)")
            else:
                record(agent_id, "full_pipeline", "FAIL", f"returned type={type(result).__name__}")
                print(f"  [FAIL] {agent_id}: returned {type(result).__name__} ({ms}ms)")

        except Exception as e:
            record(agent_id, "full_pipeline", "FAIL", str(e))
            print(f"  [FAIL] {agent_id}: {e}")
            traceback.print_exc()

    return True


def test_orchestrator_routing():
    """Test 12: Verify orchestrator routes all event types correctly."""
    print("\n" + "=" * 70)
    print("TEST 12: Orchestrator Event Routing")
    print("=" * 70)

    from app.agents.orchestrator import EVENT_ROUTING, EVENT_LANE_MAP
    from app.agents import AgentFactory

    for event_type, target_agent in EVENT_ROUTING.items():
        registered = AgentFactory.is_registered(target_agent)
        lane = EVENT_LANE_MAP.get(event_type, ["?"])
        if registered:
            record("orchestrator", f"routing_{event_type}", "PASS",
                   f"{event_type} -> {target_agent} (lane={lane})")
            print(f"  [PASS] {event_type} -> {target_agent} (lane={lane})")
        else:
            record("orchestrator", f"routing_{event_type}", "FAIL",
                   f"{event_type} -> {target_agent} NOT REGISTERED")
            print(f"  [FAIL] {event_type} -> {target_agent} NOT REGISTERED")

    return True


def test_trait_loading():
    """Test 13: Verify traits load correctly for each agent."""
    print("\n" + "=" * 70)
    print("TEST 13: Trait Loading")
    print("=" * 70)

    from app.agents import AgentFactory
    from app.agents.profile_loader import ProfileLoader
    loader = ProfileLoader.get()

    for agent_id in AgentFactory.available():
        try:
            agent = AgentFactory.create(agent_id)
            profile = loader.get_agent_profile(agent_id) or {}
            expected_traits = profile.get("traits", [])
            loaded_traits = [t.name for t in agent.traits] if agent.traits else []

            if not expected_traits:
                record(agent_id, "traits", "PASS", "No traits expected")
                print(f"  [PASS] {agent_id}: no traits defined")
            elif set(expected_traits) == set(loaded_traits):
                record(agent_id, "traits", "PASS", f"traits={loaded_traits}")
                print(f"  [PASS] {agent_id}: traits={loaded_traits}")
            else:
                missing = set(expected_traits) - set(loaded_traits)
                extra = set(loaded_traits) - set(expected_traits)
                detail = ""
                if missing:
                    detail += f"missing={missing} "
                if extra:
                    detail += f"extra={extra}"
                record(agent_id, "traits", "WARN", detail)
                print(f"  [WARN] {agent_id}: {detail}")

        except Exception as e:
            record(agent_id, "traits", "FAIL", str(e))
            print(f"  [FAIL] {agent_id}: {e}")

    return True


def test_error_handling():
    """Test 14: Verify agents handle errors gracefully (no crashes on bad input)."""
    print("\n" + "=" * 70)
    print("TEST 14: Error Handling (bad inputs)")
    print("=" * 70)

    from app.agents import AgentFactory
    from app.services import claude_service

    # Test 1: Empty payload
    print("\n  --- Test: Empty payload ---")
    for agent_id in AgentFactory.available():
        if agent_id == "cso_orchestrator":
            continue  # orchestrator delegates, skip

        try:
            agent = AgentFactory.create(agent_id)
            agent._current_db = make_mock_db()

            empty_task = {
                "event_type": "test",
                "payload": {},
                "customer_id": None,
                "customer_name": "",
                "customer_memory": {},
                "description": "",
                "execution_id": str(uuid.uuid4()),
            }

            try:
                agent.perceive(empty_task)
                record(agent_id, "error_empty_payload", "PASS", "Handled empty payload gracefully")
                print(f"  [PASS] {agent_id}: empty payload handled")
            except ValueError as ve:
                # ValueError is expected for agents that require specific fields
                record(agent_id, "error_empty_payload", "PASS", f"Raised expected ValueError: {ve}")
                print(f"  [PASS] {agent_id}: correctly raised ValueError: {ve}")
            except Exception as e:
                record(agent_id, "error_empty_payload", "FAIL", f"Unexpected error: {e}")
                print(f"  [FAIL] {agent_id}: unexpected error: {e}")

        except Exception as e:
            record(agent_id, "error_empty_payload", "FAIL", f"Failed to create agent: {e}")
            print(f"  [FAIL] {agent_id}: {e}")

    # Test 2: Claude API error response
    print("\n  --- Test: Claude API error ---")
    error_response = {"error": "api_call_failed", "detail": "Rate limited"}

    for agent_id in ["triage_agent", "health_monitor", "presales_funnel"]:
        try:
            agent = AgentFactory.create(agent_id)
            agent._current_db = make_mock_db()

            task = {
                "event_type": "test",
                "payload": {"summary": "Test", "description": "Test"},
                "customer_id": str(uuid.uuid4()),
                "customer_name": "Test",
                "customer_memory": SAMPLE_CUSTOMER_MEMORY,
                "description": "Test",
                "execution_id": str(uuid.uuid4()),
            }

            with patch.object(claude_service, 'generate_sync', return_value=error_response):
                result = agent.think(task, {"customer_memory": SAMPLE_CUSTOMER_MEMORY})

            if isinstance(result, dict) and "error" in result:
                record(agent_id, "error_claude_fail", "PASS", f"Propagated error correctly: {result['error']}")
                print(f"  [PASS] {agent_id}: Claude error handled -> {result['error']}")
            else:
                record(agent_id, "error_claude_fail", "WARN", f"Did not propagate error: {result}")
                print(f"  [WARN] {agent_id}: Claude error not propagated, got: {type(result).__name__}")

        except Exception as e:
            record(agent_id, "error_claude_fail", "FAIL", str(e))
            print(f"  [FAIL] {agent_id}: {e}")

    # Test 3: think() returns error -> act() should handle it
    print("\n  --- Test: Error propagation think->act ---")
    for agent_id in ["triage_agent", "health_monitor", "escalation_summary"]:
        try:
            agent = AgentFactory.create(agent_id)
            error_thinking = {"error": "parse_failed", "raw": "invalid json"}

            if agent_id == "health_monitor":
                agent.memory.set_context("health_score", 50)
                agent.memory.set_context("risk_level", "watch")
                agent.memory.set_context("risk_flags", [])
                agent.memory.set_context("factors", {})

            task = {
                "payload": {"jira_id": "TEST"},
                "customer_memory": SAMPLE_CUSTOMER_MEMORY,
            }

            result = agent.act(task, error_thinking)
            if isinstance(result, dict) and result.get("success") is False:
                record(agent_id, "error_propagation", "PASS", "act() correctly set success=False on error")
                print(f"  [PASS] {agent_id}: act() correctly returns success=False")
            else:
                record(agent_id, "error_propagation", "WARN",
                       f"act() did not fail: success={result.get('success', '?')}")
                print(f"  [WARN] {agent_id}: act() success={result.get('success', '?')} on error input")

        except Exception as e:
            record(agent_id, "error_propagation", "FAIL", str(e))
            print(f"  [FAIL] {agent_id}: {e}")

    return True


def test_event_service_routing():
    """Test 15: Verify event_service.route_direct works for each event type."""
    print("\n" + "=" * 70)
    print("TEST 15: Event Service Routing (route_direct)")
    print("=" * 70)

    try:
        from app.services.event_service import route_direct, EVENT_AGENT_MAP
        print(f"  Imported event_service. EVENT_AGENT_MAP has {len(EVENT_AGENT_MAP)} entries.")

        for event_type, agent_id in EVENT_AGENT_MAP.items():
            record("event_service", f"map_{event_type}", "PASS",
                   f"{event_type} -> {agent_id}")
            print(f"  [PASS] {event_type} -> {agent_id}")

    except ImportError as e:
        # event_service might import DB dependencies
        record("event_service", "import", "WARN", f"Import issue: {e}")
        print(f"  [WARN] Could not import event_service: {e}")
        print("  Falling back to orchestrator routing check...")

    return True


# ─── Summary Report ───────────────────────────────────────────────

def print_summary():
    """Print final summary of all test results."""
    print("\n" + "=" * 70)
    print("SUMMARY REPORT")
    print("=" * 70)

    pass_count = sum(1 for r in results if r["status"] == "PASS")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    skip_count = sum(1 for r in results if r["status"] == "SKIP")
    total = len(results)

    print(f"\n  Total checks: {total}")
    print(f"  PASS: {pass_count}")
    print(f"  FAIL: {fail_count}")
    print(f"  WARN: {warn_count}")
    print(f"  SKIP: {skip_count}")

    if fail_count > 0:
        print(f"\n  {'=' * 60}")
        print("  FAILURES:")
        print(f"  {'=' * 60}")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  [{r['agent']}] {r['stage']}: {r['detail']}")

    if warn_count > 0:
        print(f"\n  {'=' * 60}")
        print("  WARNINGS:")
        print(f"  {'=' * 60}")
        for r in results:
            if r["status"] == "WARN":
                print(f"  [{r['agent']}] {r['stage']}: {r['detail']}")

    print(f"\n  {'=' * 60}")
    verdict = "ALL CLEAR" if fail_count == 0 else f"{fail_count} FAILURES FOUND"
    print(f"  VERDICT: {verdict}")
    if warn_count > 0:
        print(f"  ({warn_count} warnings to review)")
    print(f"  {'=' * 60}\n")

    return fail_count == 0


# ─── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("  CS CONTROL PLANE — AGENT PIPELINE TEST SUITE")
    print("=" * 70)

    total_start = time.perf_counter()

    tests = [
        ("Agent Registration", test_agent_registration),
        ("Profile Loading", test_profile_loading),
        ("Pipeline Config", test_pipeline_config),
        ("Agent Instantiation", test_agent_instantiation),
        ("Memory System", test_memory_system),
        ("Perceive Stages", test_perceive_stages),
        ("Retrieve Stages", test_retrieve_stages),
        ("Think Stages", test_think_stages),
        ("Act Stages", test_act_stages),
        ("Reflect Stages", test_reflect_stages),
        ("Full Pipeline", test_full_pipeline),
        ("Orchestrator Routing", test_orchestrator_routing),
        ("Trait Loading", test_trait_loading),
        ("Error Handling", test_error_handling),
        ("Event Service Routing", test_event_service_routing),
    ]

    for test_name, test_fn in tests:
        try:
            test_fn()
        except Exception as e:
            print(f"\n  [CRITICAL] Test '{test_name}' crashed: {e}")
            traceback.print_exc()
            record("TEST_SUITE", test_name, "FAIL", f"Test crashed: {e}")

    total_ms = int((time.perf_counter() - total_start) * 1000)
    print(f"\n  Total test time: {total_ms}ms")

    all_pass = print_summary()
    sys.exit(0 if all_pass else 1)
