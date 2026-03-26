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
        "agents_involved": ["cso_orchestrator", "health_monitor"],
    },
    "fathom": {
        "agent_id": "health_monitor",
        "agent_name": "Dr. Aisha Okafor",
        "agents_involved": ["cso_orchestrator", "health_monitor"],
    },
    "ticket": {
        "agent_id": "triage_agent",
        "agent_name": "Kai Nakamura",
        "agents_involved": ["cso_orchestrator", "triage_agent"],
    },
    "deal": {
        "agent_id": "presales_funnel",
        "agent_name": "Jordan Reeves",
        "agents_involved": ["cso_orchestrator", "presales_funnel"],
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
        """Build the data-rich prompt based on intent, then append cross-referenced data."""
        if intent == "health":
            prompt = self._build_health_prompt(message, customer_memory)
        elif intent == "fathom":
            prompt = self._build_fathom_prompt(message, customer_memory, prefetched)
        elif intent == "ticket":
            prompt = self._build_ticket_prompt(message, customer_memory, prefetched)
        elif intent == "deal":
            prompt = self._build_deal_prompt(message, customer_memory, prefetched)
        else:
            prompt = self._build_general_prompt(message, customer_memory)

        # Append cross-referenced data from other sources (universal enrichment)
        xref_parts = []
        self._append_cross_reference(xref_parts, prefetched, existing_prompt=prompt)
        if xref_parts:
            prompt += "\n" + "\n".join(xref_parts)

        return prompt

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

        parts = [
            "## Your Role",
            "You are Dr. Aisha Okafor, the Customer Health Analyst at HivePro, also handling call intelligence analysis.",
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
                ticket_id = t.get('jira_id') or t.get('id', '?')[:8]
                cust_display = t.get('customer_name') or t.get('customer_id', '?')[:8]
                parts.append(
                    f"| {ticket_id} | {t.get('severity', t.get('priority', '?'))} | "
                    f"{t.get('status', '?')} | {t.get('title', t.get('summary', '?'))[:60]} | "
                    f"{cust_display} |"
                )
        else:
            parts.append("## No tickets found.\n")

        # Ticket stats — give Claude the authoritative counts
        ticket_info = memory.get("tickets", {})
        if ticket_info:
            parts.append(f"\n## Ticket Summary (AUTHORITATIVE — use these counts, do NOT recount manually)")
            parts.append(f"- Total tickets: {ticket_info.get('total_recent', 0)}")
            parts.append(f"- Open (including in_progress): {ticket_info.get('open_count', 0)}")
            parts.append("- IMPORTANT: The counts above are from the database and are correct. List ALL tickets from the table above.")

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

    def _build_deal_prompt(self, message: str, memory: dict, prefetched: dict) -> str:
        parts = [
            "## Your Role",
            "You are Jordan Reeves, the Pre-Sales Pipeline Analyst at HivePro.",
            "You analyze the HubSpot deals pipeline and answer questions about",
            "deal win probability, conversion rates, stalled deals, and pipeline health.",
            "",
            f"## User Question\n{message}\n",
        ]

        # Funnel metrics
        metrics = prefetched.get("funnel_metrics", {})
        if metrics:
            parts.extend([
                "## Pipeline Metrics",
                f"- Total Deals: {metrics.get('total_deals', 0)}",
                f"- Open: {metrics.get('open_deals', 0)} | Won: {metrics.get('closed_won', 0)} | Lost: {metrics.get('closed_lost', 0)}",
                f"- Overall Win Rate: {metrics.get('overall_win_rate', 0):.1%}",
                f"- Discovery -> Demo: {metrics.get('discovery_to_demo', 0):.1%}",
                f"- Demo -> POC: {metrics.get('demo_to_poc', 0):.1%}",
                f"- POC -> Close: {metrics.get('poc_to_close', 0):.1%}",
            ])

            dist = metrics.get("stage_distribution", {})
            if dist:
                parts.append("\n## Stage Distribution")
                for stage, count in sorted(dist.items(), key=lambda x: -x[1]):
                    parts.append(f"- {stage}: {count}")

        # Deal probabilities (if specific deal asked about)
        probs = prefetched.get("deal_probabilities", [])
        if probs:
            parts.append(f"\n## Deal Win Probabilities ({len(probs)} deals)")
            for p in probs[:10]:
                amt = f"${p['amount']:,.0f}" if p.get("amount") else "N/A"
                parts.append(
                    f"- **{p['deal_name']}** ({p.get('company_name', 'Unknown')}): "
                    f"{p['probability']:.0%} win probability, value: {amt}"
                )
                for f in p.get("factors", []):
                    parts.append(f"  - {f}")

        # Stalled deals
        stalled = prefetched.get("stalled_deals", [])
        if stalled:
            parts.append(f"\n## Stalled Deals ({len(stalled)} stuck >30 days)")
            for d in stalled[:10]:
                amt = f"${d['amount']:,.0f}" if d.get("amount") else "N/A"
                parts.append(
                    f"- {d['deal_name']} ({d.get('company_name', 'Unknown')}): "
                    f"stage {d['stage']}, stalled {d['days_stalled']} days, value: {amt}"
                )

        # Meeting intelligence (from ChromaDB)
        chunks = prefetched.get("meeting_chunks", [])
        if chunks:
            from collections import OrderedDict
            meetings = OrderedDict()
            for chunk in chunks:
                mid = chunk.get("meeting_id", "unknown")
                if mid not in meetings:
                    meetings[mid] = {"title": chunk.get("meeting_title", "Meeting"), "sections": {}}
                meetings[mid]["sections"][chunk.get("section_type", "")] = chunk.get("text", "")

            parts.append(f"\n## Meeting Intelligence ({len(meetings)} meetings found)")
            for mid, meeting in meetings.items():
                parts.append(f"### {meeting['title']}")
                for section_type in ["purpose", "key_takeaways", "topics", "next_steps"]:
                    text = meeting["sections"].get(section_type, "")
                    if text:
                        label = section_type.replace("_", " ").title()
                        parts.append(f"- **{label}**: {text[:400]}")
                parts.append("")

        parts.extend([
            "",
            "## Response Guidelines",
            "- ALL data above is from REAL sources (HubSpot deals, Fathom call recordings, meeting transcripts). Cite it as factual, never say 'I don't have data' when data is provided above.",
            "- Name specific companies and deals when referencing data — executives want specifics, not generalizations.",
            "- If loss analysis or call insights are provided, lead with those findings — they are the most actionable data.",
            "- If asked about a specific deal, focus on that deal's probability and the real factors driving it.",
            "- If asked about the pipeline, summarize conversion gaps with specific examples from the data.",
            "- If meeting data is available, cite specific call outcomes: who attended, what was discussed, what risks were flagged.",
            "- Always quantify: use percentages, dollar amounts, and counts.",
            "- Recommend specific actions based on the patterns in the data.",
        ])

        return "\n".join(parts)

    # ── Helpers ──────────────────────────────────────────────────────

    def _append_tickets_summary(self, parts: list, memory: dict):
        tickets = memory.get("tickets", {})
        if tickets.get("items"):
            parts.append(f"\n## Open Tickets ({tickets.get('open_count', 0)} open / {tickets.get('total_recent', 0)} total)")
            for t in tickets["items"][:5]:
                tid = t.get('jira_id') or ''
                parts.append(f"- [{t.get('severity', '?')}] {tid} {t.get('summary', 'N/A')[:80]} ({t.get('status', '?')})")

    def _append_alerts_summary(self, parts: list, memory: dict):
        alerts = memory.get("alerts", [])
        if alerts:
            parts.append(f"\n## Active Alerts ({len(alerts)})")
            for a in alerts[:5]:
                parts.append(f"- [{a.get('severity', '?')}] {a.get('title', 'N/A')} ({a.get('type', '?')})")

    def _append_cross_reference(self, parts: list, prefetched: dict, existing_prompt: str = ""):
        """Append cross-referenced data from other sources to any prompt."""
        # Related deals (for non-deal intents)
        related_deals = prefetched.get("related_deals", [])
        if related_deals:
            parts.append(f"\n## Related Deals ({len(related_deals)} found)")
            for d in related_deals[:5]:
                amt = f"${d['amount']:,.0f}" if d.get("amount") else "N/A"
                parts.append(f"- {d['deal_name']} | stage: {d['stage']} | value: {amt}")

        # Related call insights (for non-fathom intents)
        related_calls = prefetched.get("related_calls", [])
        if related_calls:
            parts.append(f"\n## Related Call Insights ({len(related_calls)} calls)")
            for c in related_calls[:5]:
                sentiment = c.get("sentiment", "?")
                parts.append(f"- [{sentiment}] {c.get('summary', 'N/A')[:200]}")
                risks = c.get("risks", [])
                if risks and isinstance(risks, list):
                    for risk in risks[:3]:
                        parts.append(f"  - RISK: {risk if isinstance(risk, str) else str(risk)[:150]}")
                decisions = c.get("decisions", [])
                if decisions and isinstance(decisions, list):
                    for dec in decisions[:2]:
                        parts.append(f"  - DECISION: {dec if isinstance(dec, str) else str(dec)[:150]}")

        # Meeting chunks — skip if already rendered in the intent-specific prompt
        chunks = prefetched.get("meeting_chunks", [])
        if chunks and "Meeting Intelligence" not in existing_prompt:
            from collections import OrderedDict
            meetings = OrderedDict()
            for chunk in chunks:
                mid = chunk.get("meeting_id", "unknown")
                if mid not in meetings:
                    meetings[mid] = {"title": chunk.get("meeting_title", "Meeting"), "sections": {}}
                meetings[mid]["sections"][chunk.get("section_type", "")] = chunk.get("text", "")

            parts.append(f"\n## Meeting Intelligence ({len(meetings)} meetings)")
            for mid, meeting in meetings.items():
                parts.append(f"### {meeting['title']}")
                for section_type in ["purpose", "key_takeaways", "topics", "next_steps"]:
                    text = meeting["sections"].get(section_type, "")
                    if text:
                        label = section_type.replace("_", " ").title()
                        parts.append(f"- **{label}**: {text[:300]}")

        # Loss analysis (deal intent only)
        loss = prefetched.get("loss_analysis", {})
        if loss.get("with_call_data", 0) > 0:
            parts.append(f"\n## Deal Loss Analysis (cross-referenced with call data)")
            parts.append(f"- Lost deals analyzed: {loss['total_lost_analyzed']}")
            parts.append(f"- Deals with call recordings: {loss['with_call_data']}")

            sentiments = loss.get("sentiment_breakdown", {})
            if sentiments:
                parts.append(f"- Sentiment of lost deal calls: positive={sentiments.get('positive', 0)}, "
                             f"negative={sentiments.get('negative', 0)}, neutral={sentiments.get('neutral', 0)}")

            topics = loss.get("top_discussion_topics", [])
            if topics:
                parts.append("- Top discussion topics in lost deals:")
                for topic, count in topics[:8]:
                    parts.append(f"  - {topic} ({count}x)")

            risks = loss.get("top_risk_themes", [])
            if risks:
                parts.append("- Risk themes from lost deal calls:")
                for risk in risks[:8]:
                    parts.append(f"  - {risk if isinstance(risk, str) else str(risk)[:150]}")

            samples = loss.get("sample_insights", [])
            if samples:
                parts.append("- Sample lost deal call insights:")
                for s in samples[:5]:
                    parts.append(f"  - **{s['company']}** [{s['sentiment']}]: {s['summary_snippet']}")

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
