"""
Orchestrator (Naveen Kapoor) — Tier 1 Supervisor.

Top-level agent that receives events, strategically decomposes them into lane-level
tasks, delegates to Lane Leads, evaluates quality, and synthesizes final output.

Pipeline: perceive → retrieve → think → act → quality_gate → finalize

Reports to: None (top of hierarchy)
Manages: support_lead, value_lead, delivery_lead
Traits: strategic_oversight, quality_evaluation, delegation, customer_sentiment
"""

import json
import logging

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent
from app.agents.memory_agent import CustomerMemoryAgent
from app.services.message_service import message_service

logger = logging.getLogger("agents.orchestrator")

# Event type → lane routing (fallback when Claude planning fails)
EVENT_LANE_MAP = {
    "jira_ticket_created": ["support"],
    "jira_ticket_updated": ["support"],
    "ticket_escalated": ["support"],
    "support_bundle_uploaded": ["support"],
    "zoom_call_completed": ["value"],
    "fathom_recording_ready": ["value"],
    "daily_health_check": ["value"],
    "manual_health_check": ["value"],
    "renewal_approaching": ["value"],
    "meeting_ended": ["value"],
    "new_enterprise_customer": ["delivery"],
    "deployment_started": ["delivery"],
    # User chat events
    "user_chat_fathom": ["value"],
    "user_chat_health": ["value"],
    "user_chat_ticket": ["support"],
    "user_chat_general": ["value", "support"],
}

LANE_LEAD_MAP = {
    "support": "support_lead",
    "value": "value_lead",
    "delivery": "delivery_lead",
}

# Backward-compat: event_type → primary specialist name (used by event_service.py)
EVENT_ROUTING = {
    "jira_ticket_created": "triage_agent",
    "jira_ticket_updated": "triage_agent",
    "ticket_escalated": "escalation_summary",
    "support_bundle_uploaded": "troubleshooter",
    "zoom_call_completed": "fathom_agent",
    "fathom_recording_ready": "fathom_agent",
    "daily_health_check": "health_monitor",
    "manual_health_check": "health_monitor",
    "renewal_approaching": "qbr_value",
    "meeting_ended": "meeting_followup",
    "new_enterprise_customer": "sow_prerequisite",
    "deployment_started": "deployment_intelligence",
    # User chat events
    "user_chat_fathom": "fathom_agent",
    "user_chat_health": "health_monitor",
    "user_chat_ticket": "triage_agent",
    "user_chat_general": "cso_orchestrator",
}


class Orchestrator(BaseAgent):
    """Tier 1 Supervisor — routes events to Lane Leads and synthesizes output."""

    agent_id = "cso_orchestrator"

    def __init__(self):
        super().__init__()
        self._memory_agent = CustomerMemoryAgent()

    def perceive(self, task: dict) -> dict:
        """Parse the event, determine urgency and scope."""
        self.memory.set_context("event_type", task.get("event_type", ""))
        self.memory.set_context("customer_id", task.get("customer_id"))
        self.memory.set_context("description", task.get("description", ""))
        self.memory.set_context("priority", task.get("priority", 5))
        return task

    def retrieve(self, task: dict) -> dict:
        """Pull customer context and past similar events."""
        context = self.memory.assemble_context(task.get("description", ""))

        # Get customer memory from Atlas (Tier 4) if not already provided
        customer_memory = task.get("customer_memory", {})
        if not customer_memory and task.get("customer_id") and self._current_db:
            customer_memory = self._memory_agent.build_memory(
                self._current_db, task["customer_id"]
            )
            task["customer_memory"] = customer_memory

        context["customer_memory"] = customer_memory
        return context

    def think(self, task: dict, context: dict) -> dict:
        """Strategic decomposition — decide which lane(s) to engage."""
        user_message = self._build_decomposition_prompt(task, context)

        trait_ctx = task.get("_trait_context", "")
        if trait_ctx:
            user_message += f"\n\n## Strategic Guidance\n{trait_ctx}"

        response = self._call_claude(user_message, max_tokens=2048, temperature=0.2)
        parsed = self._parse_claude(response)

        if "error" in parsed:
            # Fallback to event-type based routing
            return self._fallback_routing(task)

        return parsed

    def _is_chat_event(self, event_type: str) -> bool:
        """Check if this is a user chat event (should be fault-tolerant)."""
        return event_type.startswith("user_chat_")

    def act(self, task: dict, thinking: dict) -> dict:
        """Delegate to Lane Lead(s), collect deliverables."""
        lanes = thinking.get("lanes", [])
        if not lanes:
            lanes = self._fallback_routing(task).get("lanes", ["support"])

        event_type = task.get("event_type", "")
        is_chat = self._is_chat_event(event_type)
        print(f"[Orchestrator | Naveen Kapoor] act() -- delegating lanes={lanes} is_chat={is_chat}", flush=True)
        logger.info(f"[Orchestrator] Delegating: event_type={event_type}, lanes={lanes}, is_chat={is_chat}")

        deliverables = {}
        for lane in lanes:
            lead_id = LANE_LEAD_MAP.get(lane)
            if not lead_id or not AgentFactory.is_registered(lead_id):
                print(f"[Orchestrator] WARNING: Lane '{lane}' (lead_id={lead_id}) NOT REGISTERED -- skipping", flush=True)
                logger.warning(f"Lane lead '{lane}' ({lead_id}) not available, skipping")
                continue

            lead = AgentFactory.create(lead_id)

            # Extract lane-specific brief from thinking
            lane_briefs = thinking.get("lane_briefs", {})
            lane_brief = lane_briefs.get(lane, {})

            # Use brief objective for message board (much better than raw description)
            delegation_content = lane_brief.get(
                "objective",
                thinking.get(
                    "delegation_plan",
                    f"Handle {task.get('event_type', 'event')}: {task.get('description', '')[:500]}"
                ),
            )

            thread_id = None
            if self._current_db:
                try:
                    msg = message_service.send_task_assignment(
                        db_session=self._current_db,
                        from_agent=self.agent_id,
                        to_agent=lead_id,
                        content=delegation_content[:2000],
                        priority=thinking.get("priority", task.get("priority", 5)),
                        event_id=task.get("event_id"),
                        customer_id=task.get("customer_id"),
                    )
                    thread_id = msg.id
                    # Broadcast delegation event for frontend (with brief info)
                    self._broadcast_delegation("delegation:task_assigned", {
                        "from_agent": self.agent_id,
                        "to_agent": lead_id,
                        "thread_id": str(thread_id),
                        "content": delegation_content[:200],
                        "brief_objective": lane_brief.get("objective", "")[:200],
                        "brief_success_criteria": lane_brief.get("success_criteria", []),
                        "priority": thinking.get("priority", task.get("priority", 5)),
                    })
                except Exception as e:
                    logger.warning(f"Failed to record task assignment: {e}")

            # Execute lane lead with structured brief injected
            briefed_task = {
                **task,
                "task_brief": lane_brief,
                "orchestrator_rationale": thinking.get("rationale", ""),
            }
            from app.agents import demo_logger as _dl
            logger.info(_dl.delegation_start(self.agent_name, lead.agent_name, lane))
            try:
                lane_result = lead.run(
                    self._current_db,
                    briefed_task,
                    task.get("customer_memory"),
                )
                deliverables[lane] = lane_result
                logger.info(_dl.delegation_complete(lane, lane_result.get("success", False)))
            except Exception as e:
                if is_chat:
                    logger.warning(f"[Orchestrator] ╚══ Lane '{lane}' failed (non-fatal for chat): {e}")
                    deliverables[lane] = {
                        "success": False,
                        "error": str(e),
                        "skipped": True,
                        "reasoning_summary": f"Lane {lane} failed: {e}",
                    }
                    continue
                else:
                    raise

            # Record deliverable message
            if self._current_db and thread_id:
                try:
                    message_service.send_deliverable(
                        db_session=self._current_db,
                        from_agent=lead_id,
                        to_agent=self.agent_id,
                        thread_id=thread_id,
                        content=str(lane_result.get("reasoning_summary", ""))[:2000],
                        event_id=task.get("event_id"),
                        customer_id=task.get("customer_id"),
                    )
                    # Broadcast deliverable event for frontend
                    self._broadcast_delegation("delegation:deliverable", {
                        "from_agent": lead_id,
                        "to_agent": self.agent_id,
                        "thread_id": str(thread_id),
                        "content": str(lane_result.get("reasoning_summary", ""))[:200],
                    })
                except Exception as e:
                    logger.warning(f"Failed to record deliverable: {e}")

            logger.info(
                f"[orchestrator] {lane} -> success={lane_result.get('success')}"
            )

        return {"deliverables": deliverables, "lanes_used": lanes}

    def quality_gate(self, task: dict, result: dict) -> dict:
        """Evaluate quality of lane deliverables. Request rework if quality is low."""
        deliverables = result.get("deliverables", {})
        if not deliverables:
            return result

        user_message = self._build_quality_prompt(task, deliverables)
        response = self._call_claude(user_message, max_tokens=1024, temperature=0.2)
        parsed = self._parse_claude(response)

        if "error" not in parsed:
            result["quality_assessment"] = parsed

            # Rework: if quality is low AND we haven't already reworked
            quality_score = parsed.get("quality_score", 1.0)
            already_reworked = result.get("_t1_reworked", False)
            rework_lanes = parsed.get("rework_lanes", [])

            if quality_score < 0.5 and not already_reworked and rework_lanes:
                logger.info(
                    f"[Orchestrator] Quality gate FAILED (score={quality_score}). "
                    f"Requesting rework for: {rework_lanes}"
                )
                self._broadcast_delegation("delegation:quality_gate_failed", {
                    "from_agent": self.agent_id,
                    "quality_score": quality_score,
                    "issues": parsed.get("issues", []),
                    "rework_lanes": rework_lanes,
                })

                # Re-run failing lanes with feedback
                issues_str = "; ".join(parsed.get("issues", []))
                for lane in rework_lanes:
                    lead_id = LANE_LEAD_MAP.get(lane)
                    if not lead_id or not AgentFactory.is_registered(lead_id):
                        continue

                    lead = AgentFactory.create(lead_id)
                    rework_task = {
                        **task,
                        "is_rework": True,
                        "rework_feedback": issues_str,
                        "task_brief": task.get("task_brief", {}),
                    }

                    try:
                        rework_result = lead.run(
                            self._current_db, rework_task, task.get("customer_memory")
                        )
                        rework_result["was_reworked_by_t1"] = True
                        deliverables[lane] = rework_result
                    except Exception as e:
                        logger.warning(f"[Orchestrator] Rework failed for {lane}: {e}")

                result["deliverables"] = deliverables
                result["_t1_reworked"] = True

                self._broadcast_delegation("delegation:quality_gate_result", {
                    "from_agent": self.agent_id,
                    "quality_score": quality_score,
                    "reworked": True,
                    "rework_lanes": rework_lanes,
                })

        return result

    def finalize(self, task: dict, result: dict) -> dict:
        """Synthesize all lane outputs into final result."""
        deliverables = result.get("deliverables", {})

        if not deliverables:
            return {
                "success": False,
                "error": "No lane deliverables to synthesize",
                "reasoning_summary": "No lanes produced output.",
            }

        user_message = self._build_synthesis_prompt(task, result)
        response = self._call_claude(user_message, max_tokens=3000, temperature=0.3)
        parsed = self._parse_claude(response)

        if "error" in parsed:
            # Fallback: return raw deliverables
            return {
                "success": True,
                "deliverables": deliverables,
                "quality_assessment": result.get("quality_assessment", {}),
                "reasoning_summary": "Synthesis failed; raw lane deliverables returned.",
            }

        return {
            "success": True,
            **parsed,
            "deliverables": deliverables,
            "quality_assessment": result.get("quality_assessment", {}),
            "lanes_used": result.get("lanes_used", []),
            "reasoning_summary": parsed.get("summary", "Event processed successfully."),
        }

    # ── Prompt Building ──────────────────────────────────────────────

    def _build_decomposition_prompt(self, task: dict, context: dict) -> str:
        customer_memory = context.get("customer_memory", {})
        customer = customer_memory.get("customer", {})
        description = task.get("description", "")
        event_type = task.get("event_type", "")

        parts = [
            "## Incoming Event",
            f"Event Type: {event_type}",
            f"Description: {description[:1000]}",
            f"Source: {task.get('source', 'api')}",
            "",
            "## Customer Context",
            f"Customer: {customer.get('name', 'Unknown')}",
            f"Industry: {customer.get('industry', 'N/A')} | Tier: {customer.get('tier', 'N/A')}",
            f"Health: {customer_memory.get('health', {}).get('current_score', 'N/A')}",
            f"Open Tickets: {customer_memory.get('tickets', {}).get('open_count', 0)}",
            "",
            "## Available Lanes",
            "- support: Ticket triage, troubleshooting, escalation (Rachel Torres)",
            "- value: Health monitoring, call analysis, QBR generation (Damon Reeves)",
            "- delivery: SOW prerequisites, deployment intelligence (Priya Mehta)",
            "",
        ]

        # Add episodic memory
        episodic = context.get("episodic", [])
        if episodic:
            parts.append("## Recent Similar Events")
            for mem in episodic[:3]:
                parts.append(f"- {mem.get('text', '')[:200]}")
            parts.append("")

        # Smart query expansion for vague/casual queries
        is_vague = len(description.split()) < 15 or event_type.startswith("user_chat_")
        if is_vague:
            parts.extend([
                "## Query Expansion Required",
                "The user's question is casual or short. You MUST expand it into specific,",
                "focused analytical sub-questions — one per lane you choose.",
                "Each lane_brief objective should be a precise investigative question,",
                "NOT a repetition of the raw user query.",
                "Example: 'how are my customers doing?' should become:",
                "  value: 'Assess health scores, trends, and risk levels across all active customers. Identify the top 3 at-risk customers.'",
                "  support: 'Report open ticket volume, SLA compliance rate, and any P1/P2 tickets needing immediate attention.'",
                "",
            ])

        parts.extend([
            "## Instructions",
            "Analyze this event and decide:",
            "1. Which lane(s) should handle it?",
            "2. What priority (1-10)?",
            "3. For EACH lane, create a structured task brief with:",
            "   - objective: What should this lane accomplish? Be specific and actionable.",
            "   - context_summary: Pre-digest the relevant context for this lane.",
            "   - data_to_examine: What specific data should they look at?",
            "   - expected_output: What keys/format should the lane's output contain?",
            "   - success_criteria: How will you evaluate their deliverable? (2-4 bullet points)",
            "",
            "Return JSON:",
            "{",
            '  "lanes": ["value"],',
            '  "priority": 7,',
            '  "rationale": "...",',
            '  "lane_briefs": {',
            '    "value": {',
            '      "objective": "Assess customer health portfolio...",',
            '      "context_summary": "User is asking about...",',
            '      "data_to_examine": ["health scores", "trends"],',
            '      "expected_output": {"summary": "string", "risk_alerts": "list"},',
            '      "success_criteria": ["Covers all active customers", "Identifies risks"]',
            "    }",
            "  }",
            "}",
        ])
        return "\n".join(parts)

    def _build_quality_prompt(self, task: dict, deliverables: dict) -> str:
        parts = [
            "## Quality Evaluation",
            f"Original Event: {task.get('event_type', '')} — {task.get('description', '')[:500]}",
            "",
            "## Lane Deliverables",
        ]
        for lane, result in deliverables.items():
            output = result.get("output", {})
            summary = result.get("reasoning_summary", str(output)[:300])
            parts.append(f"\n### {lane.title()} Lane")
            parts.append(f"Success: {result.get('success')}")
            parts.append(f"Summary: {summary}")

        parts.extend([
            "",
            "## Instructions",
            "Evaluate: Are the deliverables complete, accurate, and actionable?",
            "If a lane's output is weak, list it in rework_lanes.",
            'Return JSON: {"quality_score": 0.0-1.0, "issues": ["issue1"], "passes": true/false, "rework_lanes": []}',
        ])
        return "\n".join(parts)

    def _build_synthesis_prompt(self, task: dict, result: dict) -> str:
        deliverables = result.get("deliverables", {})
        quality = result.get("quality_assessment", {})

        parts = [
            "## Final Synthesis",
            f"Event Type: {task.get('event_type', '')}",
            f"Customer: {task.get('customer_name', 'Unknown')}",
            f"Description: {task.get('description', '')[:500]}",
            "",
            "## Lane Deliverables",
        ]
        for lane, res in deliverables.items():
            output = res.get("output", {})
            parts.append(f"\n### {lane.title()} Lane")
            parts.append(f"Success: {res.get('success')}")
            parts.append(f"Output: {json.dumps(output, default=str)[:1000]}")

        if quality:
            parts.extend([
                "",
                f"## Quality Assessment: score={quality.get('quality_score', 'N/A')}",
            ])

        parts.extend([
            "",
            "## Instructions",
            "Synthesize all lane outputs into a final result.",
            "Return JSON with: summary, key_actions, risk_level, next_steps, confidence.",
        ])
        return "\n".join(parts)

    def _fallback_routing(self, task: dict) -> dict:
        """Event-type based routing when Claude planning fails."""
        event_type = task.get("event_type", "")
        lanes = EVENT_LANE_MAP.get(event_type, ["support"])
        return {
            "lanes": lanes,
            "priority": task.get("priority", 5),
            "delegation_plan": f"Handle {event_type}: {task.get('description', '')[:500]}",
            "rationale": f"Fallback routing for {event_type}",
        }

    # ── Legacy Compatibility ─────────────────────────────────────────

    def route(self, db_session, event: dict) -> dict:
        """
        Legacy route() interface for backward compatibility.
        Maps to the new pipeline-aware run().

        Returns the specialist agent name (from EVENT_ROUTING) and extracts
        the lane-level deliverable so callers can save agent-specific outputs.
        """
        event_type = event.get("event_type", "")
        customer_id = event.get("customer_id")
        print(f"\n[Orchestrator | Naveen Kapoor] ===============================", flush=True)
        print(f"[Orchestrator | Naveen Kapoor] route() called", flush=True)
        print(f"[Orchestrator]   event_type  = {event_type}", flush=True)
        print(f"[Orchestrator]   customer_id = {customer_id}", flush=True)
        print(f"[Orchestrator]   description = {event.get('description','')[:100]}", flush=True)
        print(f"[Orchestrator]   payload keys = {list(event.get('payload', {}).keys())}", flush=True)

        # Build customer memory — per-customer or portfolio-wide
        customer_memory = {}
        if customer_id:
            print(f"[Orchestrator] Building customer memory for {customer_id}", flush=True)
            customer_memory = self._memory_agent.build_memory(db_session, customer_id)
            print(f"[Orchestrator] Customer memory built: keys={list(customer_memory.keys())}", flush=True)
        else:
            print(f"[Orchestrator] No customer_id — building portfolio memory (all customers)", flush=True)
            customer_memory = self._memory_agent.build_portfolio_memory(db_session)
            print(f"[Orchestrator] Portfolio memory built: {customer_memory.get('portfolio', {}).get('total_customers', 0)} customers", flush=True)

        result = self.run(db_session, event, customer_memory)

        # Determine the specialist that was routed to
        event_type = event.get("event_type", "")
        specialist_name = EVENT_ROUTING.get(event_type, self.agent_id)

        # Extract specialist-level result from deliverables for saving.
        # Pipeline engine wraps output: result = {success, output: {finalized}, ...}
        # The finalized output has "deliverables" inside result["output"].
        specialist_result = result
        output = result.get("output", {}) if isinstance(result, dict) else {}
        deliverables = output.get("deliverables", result.get("deliverables", {}))
        event_lanes = EVENT_LANE_MAP.get(event_type, [])
        for lane in event_lanes:
            if lane in deliverables:
                specialist_result = deliverables[lane]
                break

        print(f"[Orchestrator | Naveen Kapoor] route() done: specialist={specialist_name}, success={result.get('success')}", flush=True)
        print(f"[Orchestrator | Naveen Kapoor] ===============================\n", flush=True)

        return {
            "agent_name": specialist_name,
            "result": specialist_result,
            "orchestrator_result": result,
            "routed": True,
        }

    def get_agent(self, agent_name: str):
        """Legacy: get an agent instance by name."""
        if agent_name == "customer_memory":
            return self._memory_agent
        if AgentFactory.is_registered(agent_name):
            return AgentFactory.create(agent_name)
        return None


# Singleton for backward compat
orchestrator = Orchestrator()

AgentFactory.register("cso_orchestrator", Orchestrator)
