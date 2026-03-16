"""
Fathom Agent (Jordan Ellis) — Tier 3 Specialist (Value Lane).

Two modes of operation:
  1. TRANSCRIPT MODE: Extracts structured insights from Fathom call recordings
     (sentiment, action items, risks, topics, recap). Triggered by webhooks.
  2. KNOWLEDGE QUERY MODE: Uses agentic RAG with 5 retrieval strategies over
     a knowledge base of 128+ customer meetings. Triggered by user chat.

Reports to: Damon Reeves (value_lead)
Traits: customer_sentiment, pattern_recognition
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent
from app.models.call_insight import CallInsight

logger = logging.getLogger("agents.fathom")


class FathomAgent(BaseAgent):
    """Enhanced Fathom Agent — call intelligence + agentic RAG knowledge retrieval."""

    agent_id = "fathom_agent"

    def perceive(self, task: dict) -> dict:
        payload = task.get("payload", {})
        user_query = payload.get("user_query")
        transcript = payload.get("transcript", "")

        print(f"\n[Fathom | Jordan Ellis] perceive()", flush=True)
        print(f"[Fathom | Jordan Ellis]   user_query present : {bool(user_query)} — '{str(user_query)[:80]}'", flush=True)
        print(f"[Fathom | Jordan Ellis]   transcript present : {bool(transcript)} ({len(transcript)} chars)", flush=True)
        print(f"[Fathom | Jordan Ellis]   recent_insights cnt: {len(payload.get('recent_insights', []))}", flush=True)
        print(f"[Fathom | Jordan Ellis]   payload keys       : {list(payload.keys())}", flush=True)

        if user_query and not transcript:
            # ── Knowledge Query Mode (Agentic RAG) ────────────────────
            recent_insights = payload.get("recent_insights", [])
            print(f"[Fathom | Jordan Ellis]   MODE: knowledge_query — will use agentic RAG + {len(recent_insights)} call insights", flush=True)
            logger.info(
                f"[Fathom] perceive: mode=knowledge_query, "
                f"query='{user_query[:100]}', "
                f"insights_available={len(recent_insights)}"
            )

            self.memory.set_context("mode", "knowledge_query")
            self.memory.set_context("user_query", user_query)

            # Also build synthetic context from call insights if available
            if recent_insights:
                synthetic = self._build_synthetic_context(user_query, recent_insights)
                self.memory.set_context("call_insights_context", synthetic)
                self.memory.set_context("insights_count", len(recent_insights))
            return task

        # ── Transcript Mode (Fathom webhook path) ──────────────────
        if not transcript:
            print(f"[Fathom]   No user_query AND no transcript — raising ValueError", flush=True)
            raise ValueError("No transcript in event payload")

        print(f"[Fathom]   MODE: transcript ({len(transcript)} chars) — Fathom webhook path", flush=True)
        logger.info(
            f"[Fathom] perceive: mode=transcript, "
            f"length={len(transcript)}, "
            f"participants={payload.get('participants', [])}"
        )

        self.memory.set_context("mode", "transcript")
        self.memory.set_context("transcript", transcript[:8000])
        self.memory.set_context("participants", payload.get("participants", []))
        self.memory.set_context("duration_minutes", payload.get("duration_minutes"))
        return task

    def retrieve(self, task: dict) -> dict:
        customer_name = task.get("customer_name", "unknown")
        context = self.memory.assemble_context(
            f"call analysis for {customer_name}"
        )
        context["customer_memory"] = task.get("customer_memory", {})
        return context

    def think(self, task: dict, context: dict) -> dict:
        payload = task.get("payload", {})
        transcript = payload.get("transcript", "")
        customer = context.get("customer_memory", {}).get("customer", {})

        mode = self.memory.get_context("mode")

        if mode == "knowledge_query":
            # ── Agentic RAG Mode: Use FathomEngine ────────────────
            return self._think_knowledge_query(task, context, customer, payload)
        else:
            # ── Transcript Mode: Original Claude analysis ─────────
            return self._think_transcript(task, context, customer, payload, transcript)

    def _think_knowledge_query(self, task: dict, context: dict, customer: dict, payload: dict) -> dict:
        """Use the FathomEngine for multi-strategy RAG retrieval."""
        from app.agents.fathom_engine import FathomEngine

        user_query = self.memory.get_context("user_query") or payload.get("user_query", "")
        call_insights_ctx = self.memory.get_context("call_insights_context") or ""

        # Augment query with customer context if available
        augmented_query = user_query
        if customer.get("name"):
            augmented_query = f"[Customer: {customer.get('name')}] {user_query}"

        print(f"[Fathom] think() — knowledge_query mode, running FathomEngine", flush=True)
        logger.info(f"[Fathom] think: running FathomEngine for query: {user_query[:100]}")

        engine = FathomEngine()
        engine_result = engine.run(query=augmented_query)

        answer = engine_result.get("answer", "")
        tool_calls_made = engine_result.get("tool_calls_made", 0)
        sources = engine_result.get("sources", [])

        print(
            f"[Fathom] think() — FathomEngine done: "
            f"tool_calls={tool_calls_made}, sources={len(sources)}, "
            f"answer_len={len(answer)}", flush=True
        )

        # If we also have call insight context, blend it in
        if call_insights_ctx and answer:
            answer += f"\n\nAdditionally, based on recent call recordings:\n{call_insights_ctx[:1000]}"

        return {
            "summary": answer,
            "sentiment": "neutral",
            "sentiment_score": 0.5,
            "key_topics": [s.get("category", "") for s in sources[:5] if s.get("category")],
            "action_items": [],
            "decisions": [],
            "risks": [],
            "sources": sources,
            "tool_calls_made": tool_calls_made,
            "mode": "knowledge_query",
        }

    def _think_transcript(self, task: dict, context: dict, customer: dict, payload: dict, transcript: str) -> dict:
        """Original transcript analysis using Claude."""
        user_message = self._build_prompt(transcript, customer, payload)

        # Enrich with episodic memory
        episodic = context.get("episodic", [])
        if episodic:
            user_message += "\n\n## Past Similar Call Analyses\n"
            for mem in episodic[:3]:
                user_message += f"- {mem.get('text', '')[:200]}\n"

        trait_ctx = task.get("_trait_context", "")
        if trait_ctx:
            user_message += f"\n\n## Agent Guidance\n{trait_ctx}"

        user_message = self._prepend_brief(user_message, task)
        print(f"[Fathom] think() — transcript mode, calling Claude: prompt={len(user_message)} chars", flush=True)
        logger.info(f"[Fathom] think: calling Claude with {len(user_message)} char prompt (mode=transcript)")
        response = self._call_claude(user_message, max_tokens=3000, temperature=0.3)
        result = self._parse_claude(response)
        print(
            f"[Fathom] think() — Claude done: sentiment={result.get('sentiment', '?')} "
            f"topics={len(result.get('key_topics', []))} error={'error' in result}", flush=True
        )
        return result

    def act(self, task: dict, thinking: dict) -> dict:
        if "error" in thinking:
            logger.warning(f"[Fathom] act: error in thinking stage: {thinking.get('error')}")
            return {"success": False, **thinking}

        mode = thinking.get("mode", "transcript")
        logger.info(
            f"[Fathom] act: success=True, mode={mode}, "
            f"sentiment={thinking.get('sentiment', '?')}, "
            f"{len(thinking.get('key_topics', []))} topics, "
            f"{len(thinking.get('action_items', []))} action items"
        )
        return {
            "success": True,
            **thinking,
            "reasoning_summary": (
                f"Fathom analysis complete (mode={mode}): "
                f"sentiment={thinking.get('sentiment', '?')}, "
                f"{len(thinking.get('key_topics', []))} topics, "
                f"{len(thinking.get('action_items', []))} action items."
            ),
        }

    # ── DB Save ──────────────────────────────────────────────────────

    def save_insight(self, db_session, customer_id, event_payload: dict, result: dict) -> None:
        """Create a CallInsight record from agent output."""
        output = self._extract_structured_output(result)

        # Use actual meeting date from Fathom API, fall back to now()
        raw_date = event_payload.get("call_date")
        if isinstance(raw_date, str) and raw_date:
            try:
                call_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                call_date = datetime.now(timezone.utc)
        elif isinstance(raw_date, datetime):
            call_date = raw_date
        else:
            call_date = datetime.now(timezone.utc)

        insight = CallInsight(
            id=uuid.uuid4(),
            customer_id=customer_id,
            fathom_recording_id=event_payload.get("recording_id"),
            call_date=call_date,
            participants=event_payload.get("participants", []),
            summary=output.get("summary"),
            decisions=output.get("decisions", []),
            action_items=output.get("action_items", []),
            risks=output.get("risks", []),
            sentiment=output.get("sentiment"),
            sentiment_score=output.get("sentiment_score"),
            key_topics=output.get("key_topics", []),
            customer_recap_draft=output.get("customer_recap_draft"),
            raw_transcript=event_payload.get("transcript"),
        )
        db_session.add(insight)
        db_session.commit()

    def _extract_structured_output(self, result: dict) -> dict:
        """
        Navigate nested pipeline output to find the raw Fathom fields.

        When routed through orchestrator -> value_lead -> fathom_agent,
        the structured output (sentiment, topics, etc.) is nested inside
        specialist_outputs. This method digs through the nesting.
        """
        # Direct result from act() — has sentiment at top level
        if result.get("sentiment"):
            return result

        output = result.get("output", result)
        if isinstance(output, dict) and output.get("sentiment"):
            return output

        # Check specialist_outputs (value lead wrapping)
        for container in (output, result):
            if not isinstance(container, dict):
                continue
            spec_outputs = container.get("specialist_outputs", {})
            for key in ("fathom", "fathom_agent"):
                spec = spec_outputs.get(key, {})
                if not isinstance(spec, dict):
                    continue
                # Pipeline engine wraps in {"success", "output", ...}
                spec_out = spec.get("output", spec)
                if isinstance(spec_out, dict):
                    # Double-wrapped: output.output
                    inner = spec_out.get("output", spec_out)
                    if isinstance(inner, dict) and inner.get("sentiment"):
                        return inner
                    if spec_out.get("sentiment"):
                        return spec_out

        # Fallback: use whatever we got
        return output if isinstance(output, dict) else result

    # ── Synthetic Context for Call Insights ────────────────────────────

    def _build_synthetic_context(self, user_query: str, insights: list[dict]) -> str:
        """Build a synthetic context string from pre-fetched CallInsight records."""
        parts = [f"User is asking: {user_query}", "", "Recent call insights:"]
        for i, insight in enumerate(insights[:5], 1):
            parts.append(f"\n--- Call {i} ({insight.get('call_date', 'N/A')}) ---")
            parts.append(f"Summary: {insight.get('summary', 'N/A')}")
            parts.append(
                f"Sentiment: {insight.get('sentiment', 'N/A')} "
                f"({insight.get('sentiment_score', 'N/A')})"
            )
            topics = insight.get("key_topics", [])
            if topics:
                parts.append(f"Topics: {', '.join(str(t) for t in topics)}")
            actions = insight.get("action_items", [])
            if actions:
                parts.append(f"Action items: {json.dumps(actions, default=str)}")
            decisions = insight.get("decisions", [])
            if decisions:
                parts.append(f"Decisions: {', '.join(str(d) for d in decisions)}")
            risks = insight.get("risks", [])
            if risks:
                parts.append(f"Risks: {', '.join(str(r) for r in risks)}")
        return "\n".join(parts)

    # ── Prompt Building (Transcript Mode) ─────────────────────────────

    def _build_prompt(self, transcript: str, customer: dict, payload: dict) -> str:
        """Build prompt for transcript analysis mode (Fathom webhook)."""
        parts = [
            "## Customer Context",
            f"Customer: {customer.get('name', 'Unknown')}",
            f"Industry: {customer.get('industry', 'N/A')} | Tier: {customer.get('tier', 'N/A')}",
            "",
            "## Call Details",
            f"Title: {payload.get('title', 'N/A')}",
            f"Participants: {', '.join(payload.get('participants', ['Unknown']))}",
            f"Duration: {payload.get('duration_minutes', 'N/A')} minutes",
            "",
            "## Transcript",
            transcript[:8000],
            "",
            "## Output Format",
            "Respond with ONLY a JSON object (no markdown, no extra text). Use this exact schema:",
            '{"summary": "2-3 paragraph executive summary of the call",',
            ' "sentiment": "positive|neutral|negative|mixed",',
            ' "sentiment_score": 0.75,',
            ' "key_topics": ["topic1", "topic2"],',
            ' "action_items": [{"task": "description", "owner": "person name", "deadline": "date or null"}],',
            ' "decisions": ["decision1", "decision2"],',
            ' "risks": ["risk1", "risk2"],',
            ' "customer_recap_draft": "Brief recap suitable to send to the customer"}',
        ]
        return "\n".join(parts)


AgentFactory.register("fathom_agent", FathomAgent)
