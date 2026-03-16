"""
Chat Fast Path — Single-call response engine for interactive chat.

Bypasses the full T1→T2→T3→T2→T1 pipeline. Instead:
1. Uses pre-assembled DB context from chat_service prefetch
2. Builds a rich prompt with all relevant data inline
3. Makes ONE Claude Haiku call (1-3s)
4. Returns formatted answer with agent attribution

The full pipeline continues to run for background events (Jira webhooks, cron, etc.).
"""

import json
import logging
import time

from app.services import claude_service

logger = logging.getLogger("services.chat_fast_path")

# Agent mapping per intent (for UI attribution)
INTENT_AGENT_MAP = {
    "health": {
        "agent_id": "health_monitor",
        "agent_name": "Dr. Aisha Okafor",
        "agents_involved": ["cso_orchestrator", "health_monitor", "value_lead"],
    },
    "fathom": {
        "agent_id": "fathom_agent",
        "agent_name": "Jordan Ellis",
        "agents_involved": ["cso_orchestrator", "fathom_agent", "value_lead"],
    },
    "ticket": {
        "agent_id": "triage_agent",
        "agent_name": "Kai Nakamura",
        "agents_involved": ["cso_orchestrator", "support_lead", "triage_agent"],
    },
    "general": {
        "agent_id": "cso_orchestrator",
        "agent_name": "Naveen Kapoor",
        "agents_involved": ["cso_orchestrator"],
    },
}

SYSTEM_PROMPT = """You are an AI Customer Success analyst for HivePro. You have access to REAL customer data provided below.

RULES:
- Give concise, actionable answers based on the data provided
- Use markdown formatting: **bold** for key metrics, bullet points for lists
- Always cite specific data points (scores, dates, ticket IDs) from the context
- If asked about a specific customer, focus your answer on that customer
- If asked a portfolio-wide question, rank/compare customers using the data
- Keep answers under 500 words unless the question requires detailed analysis
- Do NOT say you lack data — you have the full database context below"""


class ChatFastPath:
    """Single-call fast response engine for interactive chat."""

    def answer(
        self,
        message: str,
        intent: str,
        customer_name: str | None,
        customer_memory: dict,
        prefetched: dict,
        conversation_history: list[dict] | None = None,
    ) -> dict | None:
        """
        Generate a fast answer using a single Claude Haiku call.

        Returns dict with {answer, agent_id, agents_involved, model, duration_ms}
        or None if the fast path cannot handle this query (falls through to full pipeline).
        """
        start = time.perf_counter()

        logger.info(
            f"[FastPath] Building prompt: intent={intent}, customer={customer_name or 'None'}, "
            f"prefetched_keys={list(prefetched.keys())}"
        )

        # Build intent-specific prompt
        prompt = self._build_prompt(message, intent, customer_name, customer_memory, prefetched)

        # Add conversation history for follow-up coherence
        history_count = 0
        if conversation_history:
            history_count = len(conversation_history)
            history_text = self._format_history(conversation_history)
            prompt = f"{history_text}\n\n{prompt}"

        logger.info(
            f"[FastPath] Prompt ready: {len(prompt)} chars, {history_count} history messages"
        )
        logger.info(
            f"[FastPath] Calling Claude: model=claude-haiku-4-5-20251001, max_tokens=2048, temp=0.3"
        )

        # Single Claude call
        response = claude_service.generate_fast_sync(
            system_prompt=SYSTEM_PROMPT,
            user_message=prompt,
            max_tokens=2048,
            temperature=0.3,
        )

        duration_ms = int((time.perf_counter() - start) * 1000)

        if "error" in response:
            logger.warning(f"[FastPath] Claude call failed ({duration_ms}ms): {response.get('detail', response['error'])}")
            return None  # Fall through to full pipeline

        content = response["content"]
        agent_info = INTENT_AGENT_MAP.get(intent, INTENT_AGENT_MAP["general"])

        logger.info(
            f"[FastPath] {intent} query answered in {duration_ms}ms "
            f"(in:{response.get('input_tokens',0)}/out:{response.get('output_tokens',0)} tokens, "
            f"model={response.get('model','')})"
        )

        return {
            "answer": content,
            "agent_id": agent_info["agent_id"],
            "agent_name": agent_info["agent_name"],
            "agents_involved": agent_info["agents_involved"],
            "model": response.get("model", ""),
            "duration_ms": duration_ms,
            "input_tokens": response.get("input_tokens", 0),
            "output_tokens": response.get("output_tokens", 0),
        }

    # ── Prompt Builders ──────────────────────────────────────────────

    def _build_prompt(
        self,
        message: str,
        intent: str,
        customer_name: str | None,
        customer_memory: dict,
        prefetched: dict,
    ) -> str:
        """Build the data-rich prompt based on intent."""
        if intent == "health":
            return self._build_health_prompt(message, customer_memory)
        elif intent == "fathom":
            return self._build_fathom_prompt(message, customer_memory, prefetched)
        elif intent == "ticket":
            return self._build_ticket_prompt(message, customer_memory, prefetched)
        else:
            return self._build_general_prompt(message, customer_memory)

    def _build_health_prompt(self, message: str, memory: dict) -> str:
        parts = [f"## User Question\n{message}\n"]

        portfolio = memory.get("portfolio")
        if portfolio:
            parts.append(f"## Customer Portfolio ({portfolio['total_customers']} customers)\n")
            parts.append("| Customer | Health Score | Risk Level | Tier | Renewal Date |")
            parts.append("|----------|-------------|------------|------|--------------|")
            for c in portfolio.get("customers", []):
                parts.append(
                    f"| {c['name']} | {c.get('health_score', 'N/A')}/100 | "
                    f"{c.get('risk_level', '?')} | {c.get('tier', '?')} | "
                    f"{c.get('renewal_date', 'N/A')} |"
                )

            at_risk = portfolio.get("at_risk", [])
            if at_risk:
                parts.append(f"\n## At-Risk Customers ({len(at_risk)})")
                for c in at_risk:
                    flags = ", ".join(c.get("risk_flags", [])) or "none flagged"
                    parts.append(f"- **{c['name']}**: score={c.get('health_score')}, risk_flags: {flags}")
        else:
            # Single customer
            customer = memory.get("customer", {})
            health = memory.get("health", {})
            parts.append(f"## Customer: {customer.get('name', 'Unknown')}")
            parts.append(f"- Industry: {customer.get('industry', 'N/A')}, Tier: {customer.get('tier', 'N/A')}")
            parts.append(f"- Health Score: {health.get('current_score', 'N/A')}/100")
            parts.append(f"- Risk Level: {health.get('risk_level', 'N/A')}")
            parts.append(f"- Risk Flags: {', '.join(health.get('risk_flags', [])) or 'None'}")
            parts.append(f"- Renewal: {customer.get('renewal_date', 'N/A')}")

            trend = health.get("trend", [])
            if trend:
                parts.append("\n## Health Trend (last 30 days)")
                for t in trend[-10:]:
                    parts.append(f"- {t.get('date', '?')}: {t.get('score', '?')}/100")

        # Add tickets and alerts summary
        self._append_tickets_summary(parts, memory)
        self._append_alerts_summary(parts, memory)

        return "\n".join(parts)

    def _build_fathom_prompt(self, message: str, memory: dict, prefetched: dict) -> str:
        import json as _json

        parts = [
            "## Your Role",
            "You are Jordan Ellis, the Call Intelligence Specialist at HivePro.",
            "Provide executive-grade meeting intelligence — deeper and more actionable ",
            "than any recording tool's built-in summary.",
            "",
            "## Response Format (Slack-optimized)",
            "Structure your response with these sections. Use --- between sections.",
            "Keep total response under 800 words — be concise and high-impact.",
            "",
            "1. **TL;DR** — 2-3 sentences, most important takeaway first",
            "",
            "2. **Key Discussions** — Per call: one bold title line + 2-3 bullet points max.",
            "   Format: **Call N (Date) — Customer: Topic**",
            "",
            "3. **Decisions & Commitments** — Bullet list:",
            "   - 🔵 [Owner] Decision — Deadline",
            "",
            "4. **Action Items** — Bullet list with priority emoji:",
            "   - 🔴 [Owner] Task — Deadline (HIGH)",
            "   - 🟡 [Owner] Task — Deadline (MEDIUM)",
            "   - 🟢 [Owner] Task — no deadline (LOW)",
            "",
            "5. **Risk Signals** — Grouped by severity:",
            "   🔴 *CRITICAL*: One-line risk description",
            "   🟠 *HIGH*: One-line risk description",
            "   🟡 *MEDIUM*: One-line risk description",
            "",
            "6. **Sentiment** — Bullet list with trajectory emoji:",
            "   - Call N: Positive (0.72) 📈 Improving — one-line note",
            "   - Overall: Brief portfolio assessment",
            "",
            "7. **Next Steps** — 3-5 numbered actions, most urgent first",
            "",
            "## FORMATTING RULES",
            "- NEVER use markdown tables (| col | col |) — they break in Slack",
            "- Use bullet lists with emoji instead of tables",
            "- Keep each section to 3-5 bullets max",
            "- Use **bold** for names, dates, and key terms",
            "- Use --- between major sections for visual breaks",
            "- Cross-reference across multiple calls to spot trends",
            "- Highlight negative or declining sentiment prominently",
            "- Be specific: use names, dates, numbers from the data",
            "- Don't just summarize — analyze and recommend",
            "",
            f"## User Question\n{message}\n",
        ]

        # Use ChromaDB meeting knowledge chunks (155+ real meetings)
        chunks = prefetched.get("meeting_chunks", [])

        logger.info(f"[FastPath] Meeting knowledge: {len(chunks)} chunks from ChromaDB")

        if chunks:
            # Group chunks by meeting_id for structured display
            from collections import OrderedDict
            meetings = OrderedDict()
            for chunk in chunks:
                mid = chunk.get("meeting_id", "unknown")
                if mid not in meetings:
                    meetings[mid] = {
                        "title": chunk.get("meeting_title", "Unknown Meeting"),
                        "category": chunk.get("category", ""),
                        "sections": {},
                    }
                meetings[mid]["sections"][chunk.get("section_type", "")] = chunk.get("text", "")

            parts.append(f"## Meeting Data ({len(meetings)} meetings from knowledge base)\n")
            for i, (mid, meeting) in enumerate(meetings.items(), 1):
                title = meeting["title"]
                category = meeting["category"]
                logger.info(f"[FastPath]   Meeting {i}: {title} ({category})")
                parts.append(f"### Meeting {i}: {title}")
                parts.append(f"- **Category**: {category}")

                for section_type in ["purpose", "key_takeaways", "topics", "next_steps"]:
                    text = meeting["sections"].get(section_type, "")
                    if text:
                        label = section_type.replace("_", " ").title()
                        parts.append(f"- **{label}**:\n{text}")

                parts.append("")
        else:
            parts.append("## No matching meeting data found in knowledge base.\n")

        # Customer context
        customer = memory.get("customer", {})
        if customer.get("name"):
            parts.append(f"## Customer Context: {customer.get('name', 'Unknown')} (Tier: {customer.get('tier', '?')})")
            if customer.get("industry"):
                parts.append(f"- Industry: {customer['industry']}")
            if customer.get("renewal_date"):
                parts.append(f"- Renewal: {customer['renewal_date']}")

        return "\n".join(parts)

    def _build_ticket_prompt(self, message: str, memory: dict, prefetched: dict) -> str:
        parts = [f"## User Question\n{message}\n"]

        tickets = prefetched.get("recent_tickets", [])
        if not tickets:
            tickets = memory.get("tickets", {}).get("items", [])

        if tickets:
            parts.append(f"## Tickets ({len(tickets)} total)\n")
            parts.append("| ID | Severity | Status | Summary | Customer |")
            parts.append("|----|----------|--------|---------|----------|")
            for t in tickets[:20]:
                cust_display = t.get('customer_name') or t.get('customer_id', '?')[:8]
                parts.append(
                    f"| {t.get('id', '?')[:8]} | {t.get('severity', t.get('priority', '?'))} | "
                    f"{t.get('status', '?')} | {t.get('title', t.get('summary', '?'))[:60]} | "
                    f"{cust_display} |"
                )
        else:
            parts.append("## No tickets found.\n")

        # Ticket stats
        ticket_info = memory.get("tickets", {})
        if ticket_info:
            parts.append(f"\n## Ticket Summary")
            parts.append(f"- Total recent: {ticket_info.get('total_recent', 0)}")
            parts.append(f"- Open: {ticket_info.get('open_count', 0)}")

        return "\n".join(parts)

    def _build_general_prompt(self, message: str, memory: dict) -> str:
        parts = [f"## User Question\n{message}\n"]

        # Include everything available
        portfolio = memory.get("portfolio")
        if portfolio:
            parts.append(f"## Portfolio Overview ({portfolio['total_customers']} customers)")
            at_risk = portfolio.get("at_risk", [])
            watch = portfolio.get("watch_list", [])
            healthy = [c for c in portfolio.get("customers", []) if c.get("risk_level") == "healthy"]

            if at_risk:
                parts.append(f"\n### At-Risk ({len(at_risk)})")
                for c in at_risk:
                    parts.append(f"- **{c['name']}**: score={c.get('health_score')}, tier={c.get('tier')}")
            if watch:
                parts.append(f"\n### Watch List ({len(watch)})")
                for c in watch:
                    parts.append(f"- **{c['name']}**: score={c.get('health_score')}, tier={c.get('tier')}")
            if healthy:
                parts.append(f"\n### Healthy ({len(healthy)})")
                for c in healthy:
                    parts.append(f"- {c['name']}: score={c.get('health_score')}")
        else:
            customer = memory.get("customer", {})
            if customer.get("name"):
                parts.append(f"## Customer: {customer['name']}")
                parts.append(f"- Tier: {customer.get('tier', '?')}, Industry: {customer.get('industry', '?')}")

        # Health overview
        health = memory.get("health", {})
        if health.get("current_score"):
            parts.append(f"\n## Health: {health['current_score']}/100 ({health.get('risk_level', '?')})")

        self._append_tickets_summary(parts, memory)
        self._append_alerts_summary(parts, memory)

        # Call insights summary
        calls = memory.get("calls", {})
        if calls.get("items"):
            parts.append(f"\n## Recent Calls ({calls.get('total_recent', 0)})")
            for c in calls["items"][:3]:
                parts.append(f"- [{c.get('sentiment', '?')}] {c.get('summary', 'N/A')[:100]}")

        return "\n".join(parts)

    # ── Helpers ──────────────────────────────────────────────────────

    def _append_tickets_summary(self, parts: list, memory: dict):
        tickets = memory.get("tickets", {})
        if tickets.get("items"):
            parts.append(f"\n## Open Tickets ({tickets.get('open_count', 0)} open / {tickets.get('total_recent', 0)} total)")
            for t in tickets["items"][:5]:
                parts.append(f"- [{t.get('severity', '?')}] {t.get('summary', 'N/A')[:80]} ({t.get('status', '?')})")

    def _append_alerts_summary(self, parts: list, memory: dict):
        alerts = memory.get("alerts", [])
        if alerts:
            parts.append(f"\n## Active Alerts ({len(alerts)})")
            for a in alerts[:5]:
                parts.append(f"- [{a.get('severity', '?')}] {a.get('title', 'N/A')} ({a.get('type', '?')})")

    def _format_history(self, messages: list[dict]) -> str:
        if not messages:
            return ""
        parts = ["## Conversation History"]
        for msg in messages[-5:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:300]
            parts.append(f"**{role}:** {content}")
        return "\n".join(parts)


# Singleton
chat_fast_path = ChatFastPath()
