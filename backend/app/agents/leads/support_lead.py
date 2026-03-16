"""
Support Lead (Rachel Torres) — Tier 2 Lane Lead.

Coordinates the Support lane: Triage → Troubleshooter → Escalation.
Reports to: Naveen Kapoor (cso_orchestrator)
Manages: triage_agent, troubleshooter, escalation_summary
Traits: sla_awareness, delegation, quality_evaluation
"""

import json
import logging

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent
from app.services.message_service import message_service

logger = logging.getLogger("agents.support_lead")

# Maps thinking output keys to agent IDs
SPECIALIST_MAP = {
    "triage": "triage_agent",
    "troubleshoot": "troubleshooter",
    "escalation": "escalation_summary",
}


class SupportLead(BaseAgent):
    """Tier 2 Lane Lead for the Support lane."""

    agent_id = "support_lead"

    def perceive(self, task: dict) -> dict:
        self.memory.set_context("task_description", task.get("description", ""))
        self.memory.set_context("priority", task.get("priority", 5))
        self.memory.set_context("event_type", task.get("event_type", ""))
        return task

    def retrieve(self, task: dict) -> dict:
        context = self.memory.assemble_context(task.get("description", ""))
        context["customer_memory"] = task.get("customer_memory", {})
        return context

    def think(self, task: dict, context: dict) -> dict:
        """Plan which specialists to engage and in what order."""
        user_message = self._build_planning_prompt(task, context)

        trait_ctx = task.get("_trait_context", "")
        if trait_ctx:
            user_message += f"\n\n## Lead Guidance\n{trait_ctx}"

        response = self._call_claude(user_message, max_tokens=1024, temperature=0.2)
        parsed = self._parse_claude(response)
        if "error" in parsed:
            # Fallback: route based on event type
            return self._fallback_plan(task)
        return parsed

    def act(self, task: dict, thinking: dict) -> dict:
        """Coordinate specialists with structured briefs, validate, and rework if needed."""
        specialist_names = thinking.get("specialists", [])
        if not specialist_names:
            specialist_names = self._fallback_plan(task).get("specialists", ["triage"])

        specialist_outputs = {}
        for spec_key in specialist_names:
            agent_id = SPECIALIST_MAP.get(spec_key)
            if not agent_id or not AgentFactory.is_registered(agent_id):
                logger.warning(f"Specialist '{spec_key}' ({agent_id}) not available, skipping")
                continue

            specialist = AgentFactory.create(agent_id)

            # Extract specialist-specific brief from thinking
            spec_brief = thinking.get("specialist_briefs", {}).get(spec_key, {})

            # Build enriched event with brief
            enriched_event = {
                **task,
                "lane_lead_plan": thinking,
                "prior_outputs": specialist_outputs,
                "specialist_brief": spec_brief,
            }

            # Record task assignment with brief objective
            brief_objective = spec_brief.get("objective", f"Assigned {spec_key}: {task.get('description', '')[:500]}")
            thread_id = None
            if self._current_db:
                try:
                    msg = message_service.send_task_assignment(
                        db_session=self._current_db,
                        from_agent=self.agent_id,
                        to_agent=agent_id,
                        content=brief_objective[:2000],
                        priority=task.get("priority", 5),
                        event_id=task.get("event_id"),
                        customer_id=task.get("customer_id"),
                    )
                    thread_id = msg.id
                    self._broadcast_delegation("delegation:task_assigned", {
                        "from_agent": self.agent_id,
                        "to_agent": agent_id,
                        "brief_objective": brief_objective[:200],
                        "brief_success_criteria": spec_brief.get("success_criteria", []),
                    })
                except Exception as e:
                    logger.warning(f"Failed to record task assignment: {e}")

            # Execute specialist
            result = specialist.run(self._current_db, enriched_event, task.get("customer_memory"))

            # Validate output against brief (cost-aware)
            validation = self._validate_output(spec_key, spec_brief, result, task)
            result["validation"] = validation

            if not validation.get("passes", True) and validation.get("score", 1.0) < 0.6:
                logger.info(f"[support_lead] Requesting rework from {spec_key}: {validation.get('feedback', '')[:100]}")

                self._broadcast_delegation("delegation:rework_requested", {
                    "from_agent": self.agent_id,
                    "to_agent": agent_id,
                    "feedback": validation.get("feedback", "")[:200],
                    "score": validation.get("score", 0),
                })

                # Record feedback on message board
                if self._current_db and thread_id:
                    try:
                        message_service.send_feedback(
                            db_session=self._current_db,
                            from_agent=self.agent_id,
                            to_agent=agent_id,
                            thread_id=thread_id,
                            content=f"Rework needed: {validation.get('feedback', '')}",
                            event_id=task.get("event_id"),
                            customer_id=task.get("customer_id"),
                        )
                    except Exception as e:
                        logger.warning(f"Failed to record feedback: {e}")

                # ONE rework round
                rework_event = {
                    **enriched_event,
                    "is_rework": True,
                    "rework_feedback": validation.get("feedback", ""),
                    "rework_missing": validation.get("missing", []),
                }
                result = specialist.run(self._current_db, rework_event, task.get("customer_memory"))
                result["was_reworked"] = True
                result["rework_feedback"] = validation.get("feedback", "")

            # Check for auto-escalation (low confidence)
            reflection = result.get("reflection", {})
            if isinstance(reflection, dict):
                confidence = reflection.get("confidence", 1.0)
                should_escalate = reflection.get("should_escalate", False)
                if should_escalate or confidence < 0.4:
                    escalation_reason = reflection.get("escalation_reason", f"Low confidence ({confidence:.0%})")
                    logger.warning(f"[support_lead] Auto-escalation for {spec_key}: {escalation_reason}")
                    self._broadcast_delegation("delegation:auto_escalation", {
                        "from_agent": self.agent_id,
                        "specialist": spec_key,
                        "confidence": confidence,
                        "reason": escalation_reason,
                    })
                    result["was_escalated"] = True

            specialist_outputs[spec_key] = result
            logger.info(f"[support_lead] {spec_key} -> success={result.get('success')}")

        return {"specialist_outputs": specialist_outputs}

    def finalize(self, task: dict, result: dict) -> dict:
        """Synthesize specialist outputs into lane deliverable."""
        specialist_outputs = result.get("specialist_outputs", {})

        if not specialist_outputs:
            return {
                "success": False,
                "error": "No specialist outputs to synthesize",
                "reasoning_summary": "No specialists produced output.",
            }

        user_message = self._build_synthesis_prompt(task, specialist_outputs)
        response = self._call_claude(user_message, max_tokens=2048, temperature=0.3)
        parsed = self._parse_claude(response)

        if "error" in parsed:
            # Fallback: return raw specialist outputs
            return {
                "success": True,
                "specialist_outputs": specialist_outputs,
                "reasoning_summary": "Lane synthesis failed; raw specialist outputs returned.",
            }

        return {
            "success": True,
            **parsed,
            "specialist_outputs": specialist_outputs,
            "reasoning_summary": parsed.get("summary", "Support lane deliverable ready."),
        }

    # ── Prompt Building ──────────────────────────────────────────────

    def _build_planning_prompt(self, task: dict, context: dict) -> str:
        customer_name = task.get("customer_name", "Unknown")
        description = task.get("description", "")
        event_type = task.get("event_type", "")
        task_brief = task.get("task_brief", {})

        parts = ["## Task Brief from Orchestrator (Naveen Kapoor)"]

        if task_brief:
            parts.extend([
                f"Objective: {task_brief.get('objective', 'N/A')}",
                f"Context: {task_brief.get('context_summary', 'N/A')}",
                f"Data to Examine: {', '.join(task_brief.get('data_to_examine', []))}",
                f"Expected Output: {json.dumps(task_brief.get('expected_output', {}), default=str)}",
                f"Success Criteria: {'; '.join(task_brief.get('success_criteria', []))}",
            ])
        else:
            parts.append(f"Description: {description[:1000]}")

        parts.extend([
            "",
            f"Event Type: {event_type}",
            f"Customer: {customer_name}",
            f"Priority: {task.get('priority', 5)}",
            "",
            "## Available Specialists",
            "- triage: Ticket classification and prioritization (Kai Nakamura)",
            "- troubleshoot: Root cause analysis and resolution (Leo Petrov)",
            "- escalation: Escalation summary for L2/L3 engineering (Maya Santiago)",
            "",
            "## Instructions",
            "Decide which specialists to engage and in what order.",
            "For EACH specialist you select, create a focused task brief:",
            'Return JSON: {"specialists": ["triage"], "rationale": "...", "specialist_briefs": {"triage": {"objective": "...", "focus_areas": ["..."], "expected_output": {"key": "format"}, "success_criteria": ["..."]}}}',
        ])
        return "\n".join(parts)

    def _build_synthesis_prompt(self, task: dict, outputs: dict) -> str:
        parts = [
            "## Support Lane Synthesis",
            f"Original Task: {task.get('description', '')[:500]}",
            f"Customer: {task.get('customer_name', 'Unknown')}",
            "",
            "## Specialist Outputs",
        ]
        for name, result in outputs.items():
            output = result.get("output", {})
            summary = result.get("reasoning_summary", str(output)[:300])
            parts.append(f"\n### {name.title()}")
            parts.append(f"Success: {result.get('success')}")
            parts.append(f"Summary: {summary}")
            parts.append(f"Output: {json.dumps(output, default=str)[:800]}")

        parts.extend([
            "",
            "## Instructions",
            "Synthesize these specialist outputs into a coherent lane deliverable.",
            "Return JSON with: summary, key_findings, recommended_actions, confidence.",
        ])
        return "\n".join(parts)

    def _fallback_plan(self, task: dict) -> dict:
        """Event-type based routing when Claude planning fails."""
        event_type = task.get("event_type", "")
        if "escalat" in event_type:
            return {"specialists": ["escalation"], "rationale": "Escalation event"}
        if "troubleshoot" in event_type or "bundle" in event_type:
            return {"specialists": ["troubleshoot"], "rationale": "Troubleshooting event"}
        # Default: triage first, then troubleshoot if it's a ticket
        if "ticket" in event_type:
            return {"specialists": ["triage", "troubleshoot"], "rationale": "Ticket event"}
        return {"specialists": ["triage"], "rationale": "Default triage"}


AgentFactory.register("support_lead", SupportLead)
