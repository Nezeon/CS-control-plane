"""
Pre-Sales Funnel Agent — Tier 3 Specialist (Pre-Sales Lane).

Analyzes the HubSpot deals pipeline to surface conversion rates,
stalled deals, blocker patterns, and deal win probability.
Deterministic SQL checks for metrics, Claude only for narrative.

Lane: Pre-Sales
Traits: pattern_recognition, trend_analysis
Answers: Q3 (POC conversion), Q11 (deal win probability)
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import text

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent

logger = logging.getLogger("agents.presales_funnel")

# Ordered pipeline stages from earliest to latest (from HubSpot "HivePro Global" pipeline)
PIPELINE_STAGES = [
    "appointmentscheduled",   # Discovery Meeting
    "presentationscheduled",  # Demo 1
    "decisionmakerboughtin",  # Demo 2
    "1166515347",             # Pre-POC
    "219679027",              # POC
    "1157536395",             # Negotiation
    "contractsent",           # Contract Sent
]

CLOSED_STAGES = ["closedwon", "closedlost"]

# Stage index for "at least reached this stage" calculations
STAGE_ORDER = {s: i for i, s in enumerate(PIPELINE_STAGES)}
STAGE_ORDER["closedwon"] = len(PIPELINE_STAGES)
STAGE_ORDER["closedlost"] = -1  # Lost deals don't advance


class PreSalesFunnelAgent(BaseAgent):
    """Analyzes HubSpot pipeline: conversion rates, stalled deals, win probability."""

    agent_id = "presales_funnel"

    # ── Deterministic Metrics ──────────────────────────────────────────

    def _compute_conversion_rates(self, db) -> dict:
        """Calculate stage-to-stage conversion rates from deals table."""
        rows = db.execute(text("""
            SELECT stage, COUNT(*) as cnt
            FROM deals
            GROUP BY stage
        """)).fetchall()

        stage_counts = {r[0]: r[1] for r in rows}
        total = sum(stage_counts.values())

        # Count deals that reached at least each stage
        won = stage_counts.get("closedwon", 0)
        lost = stage_counts.get("closedlost", 0)

        # Deals that reached each stage = deals currently at that stage + all deals past it
        # We compute "reached" by summing current + all later stages (including won)
        reached = {}
        for i, stage in enumerate(PIPELINE_STAGES):
            count = stage_counts.get(stage, 0)
            # Add all later stages
            for later in PIPELINE_STAGES[i + 1:]:
                count += stage_counts.get(later, 0)
            count += won  # Closed won deals passed through all stages
            reached[stage] = count

        # Stage-to-stage conversion = reached[next] / reached[current]
        def safe_ratio(numerator, denominator):
            return round(numerator / denominator, 3) if denominator > 0 else 0.0

        discovery = reached.get("appointmentscheduled", 0)
        demo = reached.get("presentationscheduled", 0)
        poc = reached.get("219679027", 0)

        metrics = {
            "total_deals": total,
            "closed_won": won,
            "closed_lost": lost,
            "open_deals": total - won - lost,
            "overall_win_rate": safe_ratio(won, won + lost) if (won + lost) > 0 else 0.0,
            "discovery_to_demo": safe_ratio(demo, discovery),
            "demo_to_poc": safe_ratio(poc, demo),
            "poc_to_close": safe_ratio(won, poc),
            "stage_distribution": stage_counts,
        }

        logger.info(
            f"[PreSales] Conversion rates: win_rate={metrics['overall_win_rate']}, "
            f"demo_to_poc={metrics['demo_to_poc']}, poc_to_close={metrics['poc_to_close']}"
        )
        return metrics

    def _find_stalled_deals(self, db, days_threshold: int = 30) -> list:
        """Find deals stuck in the same stage beyond threshold."""
        # Use hubspot_updated_at (HubSpot's hs_lastmodifieddate) not our updated_at
        rows = db.execute(text("""
            SELECT deal_name, stage, company_name, amount,
                   COALESCE(hubspot_updated_at, updated_at) as last_modified,
                   hubspot_deal_id
            FROM deals
            WHERE stage NOT IN ('closedwon', 'closedlost')
              AND COALESCE(hubspot_updated_at, updated_at) < NOW() - CAST(:days || ' days' AS interval)
            ORDER BY COALESCE(hubspot_updated_at, updated_at) ASC
            LIMIT 20
        """), {"days": str(days_threshold)}).fetchall()

        now = datetime.now(timezone.utc)
        stalled = []
        for r in rows:
            updated = r[4]
            if updated and updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            days_stalled = (now - updated).days if updated else days_threshold

            stalled.append({
                "deal_name": r[0],
                "stage": r[1],
                "company_name": r[2],
                "amount": r[3],
                "days_stalled": days_stalled,
                "hubspot_deal_id": r[5],
            })

        logger.info(f"[PreSales] Found {len(stalled)} stalled deals (>{days_threshold} days)")
        return stalled

    def _analyze_blockers(self, db) -> list:
        """Analyze where deals die — group closedlost by the stage they were in."""
        # For closedlost deals, the `properties` JSONB stores the last stage info
        # Since closedlost IS the stage, we look at deal age patterns instead
        rows = db.execute(text("""
            SELECT
                COALESCE(properties->>'dealstage', stage) as last_stage,
                COUNT(*) as lost_count,
                COALESCE(SUM(amount), 0) as total_value
            FROM deals
            WHERE stage = 'closedlost'
            GROUP BY COALESCE(properties->>'dealstage', stage)
            ORDER BY lost_count DESC
        """)).fetchall()

        blockers = []
        for r in rows:
            blockers.append({
                "stage": r[0],
                "lost_count": r[1],
                "total_value": float(r[2]) if r[2] else 0.0,
            })

        logger.info(f"[PreSales] Blocker analysis: {len(blockers)} stages with losses")
        return blockers

    def _compute_loss_analysis(self, db, limit: int = 20) -> dict:
        """Cross-reference closedlost deals with call insights to find WHY deals failed."""
        # Get closedlost deals with company names
        lost_deals = db.execute(text("""
            SELECT deal_name, company_name, amount, hubspot_created_at
            FROM deals
            WHERE stage = 'closedlost' AND company_name IS NOT NULL
            ORDER BY amount DESC NULLS LAST
            LIMIT :lim
        """), {"lim": limit}).fetchall()

        if not lost_deals:
            return {"total_lost_analyzed": 0, "with_call_data": 0, "insights": []}

        # For each lost deal, search call insights by company name (first word)
        insights_found = []
        companies_seen = set()

        for deal in lost_deals:
            company = deal[1]
            if not company:
                continue
            search_key = company.lower().split()[0]
            if len(search_key) < 3 or search_key in companies_seen:
                continue
            companies_seen.add(search_key)

            calls = db.execute(text("""
                SELECT summary, sentiment, risks, key_topics, decisions
                FROM call_insights
                WHERE LOWER(summary) LIKE :s
                ORDER BY processed_at DESC LIMIT 3
            """), {"s": f"%{search_key}%"}).fetchall()

            if calls:
                for call in calls:
                    risks = call[2] or []
                    topics = call[3] or []
                    sentiment = call[1]
                    insights_found.append({
                        "company": company,
                        "deal_value": deal[2],
                        "sentiment": sentiment,
                        "risks": risks if isinstance(risks, list) else [],
                        "key_topics": topics if isinstance(topics, list) else [],
                        "summary_snippet": (call[0] or "")[:200],
                    })

        # Aggregate patterns
        all_risks = []
        all_topics = []
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        for ins in insights_found:
            all_risks.extend(ins["risks"])
            all_topics.extend(ins["key_topics"])
            s = ins.get("sentiment", "neutral")
            if s in sentiment_counts:
                sentiment_counts[s] += 1

        # Count topic frequency
        from collections import Counter
        topic_freq = Counter(t.lower() if isinstance(t, str) else str(t) for t in all_topics).most_common(10)

        result = {
            "total_lost_analyzed": len(lost_deals),
            "with_call_data": len(insights_found),
            "sentiment_breakdown": sentiment_counts,
            "top_risk_themes": all_risks[:15],
            "top_discussion_topics": topic_freq,
            "sample_insights": insights_found[:10],
        }

        logger.info(
            f"[PreSales] Loss analysis: {len(lost_deals)} lost deals, "
            f"{len(insights_found)} with call data, {len(all_risks)} risks found"
        )
        return result

    def _compute_deal_probability(self, db, deal_name: str | None = None) -> list:
        """
        Multi-factor win probability using real data signals.

        Factors (weighted):
          - Pipeline stage position (25%) — how far along in the funnel
          - Meeting engagement (25%) — call count, duration, participant count
          - Buyer intent signals (20%) — decisions made, action items, requirements discussed
          - Sentiment (15%) — call sentiment from Fathom analysis
          - Deal velocity (15%) — age vs expected pace for the stage
        """
        # Stage base rates (25% weight)
        STAGE_BASE = {
            "appointmentscheduled": 0.15,
            "presentationscheduled": 0.30,
            "decisionmakerboughtin": 0.45,
            "1166515347": 0.60,   # Pre-POC
            "219679027": 0.70,    # POC
            "1157536395": 0.80,   # Negotiation
            "contractsent": 0.90, # Contract Sent
        }

        # Get open deals
        query = """
            SELECT deal_name, stage, amount, company_name, hubspot_created_at, hubspot_deal_id
            FROM deals
            WHERE stage NOT IN ('closedwon', 'closedlost')
        """
        params = {}
        if deal_name:
            query += " AND (LOWER(deal_name) LIKE :name OR LOWER(company_name) LIKE :name)"
            params["name"] = f"%{deal_name.lower()}%"
        query += " ORDER BY amount DESC NULLS LAST LIMIT 10"

        rows = db.execute(text(query), params).fetchall()

        now = datetime.now(timezone.utc)
        probabilities = []

        for r in rows:
            name = r[0]
            stage = r[1]
            amount = r[2]
            company = r[3]
            created = r[4]
            deal_id = r[5]

            factors = []
            scores = {}  # factor_name -> 0.0 to 1.0

            # ── Factor 1: Pipeline Stage (25%) ──
            stage_score = STAGE_BASE.get(stage, 0.10)
            scores["stage"] = stage_score
            factors.append(f"Stage: {stage} ({int(stage_score * 100)}% base)")

            # ── Factor 2: Meeting Engagement (25%) ──
            # Search by first meaningful word of company/deal name in call insights
            # (full names like "Marriott International" won't match "Marriott's team")
            engagement_score = 0.0
            meeting_details = []
            raw_search = (company or name or "").lower().strip()
            # Use first word if multi-word (e.g., "Marriott International" -> "marriott")
            search_term = raw_search.split()[0] if raw_search else ""
            # But skip generic words
            if search_term in ("the", "a", "an", "new", "test"):
                search_term = raw_search  # fall back to full name
            if search_term and len(search_term) >= 3:
                calls = db.execute(text("""
                    SELECT summary, sentiment, sentiment_score, participants,
                           decisions, action_items, key_topics
                    FROM call_insights
                    WHERE LOWER(summary) LIKE :search
                       OR LOWER(CAST(key_topics AS text)) LIKE :search
                    ORDER BY processed_at DESC LIMIT 5
                """), {"search": f"%{search_term}%"}).fetchall()

                if calls:
                    call_count = len(calls)
                    total_participants = 0
                    for call in calls:
                        participants = call[3] or []
                        if isinstance(participants, list):
                            total_participants += len(participants)

                    # More calls = more engagement
                    if call_count >= 3:
                        engagement_score = 0.9
                    elif call_count >= 2:
                        engagement_score = 0.7
                    else:
                        engagement_score = 0.5

                    # Many participants = decision-makers involved
                    avg_participants = total_participants / call_count if call_count else 0
                    if avg_participants >= 5:
                        engagement_score = min(engagement_score + 0.1, 1.0)
                        meeting_details.append(f"avg {avg_participants:.0f} participants (decision-makers likely)")

                    factors.append(f"Meetings: {call_count} calls found ({int(engagement_score * 100)}% engagement)")
                else:
                    factors.append("Meetings: none found (0% engagement)")

            scores["engagement"] = engagement_score

            # ── Factor 3: Buyer Intent Signals (20%) ──
            intent_score = 0.0
            if search_term and len(search_term) >= 3:
                # Reuse calls from above if available
                intent_signals = []
                calls_for_intent = db.execute(text("""
                    SELECT decisions, action_items, key_topics, summary
                    FROM call_insights
                    WHERE LOWER(summary) LIKE :search
                       OR LOWER(CAST(key_topics AS text)) LIKE :search
                    ORDER BY processed_at DESC LIMIT 5
                """), {"search": f"%{search_term}%"}).fetchall()

                total_decisions = 0
                total_actions = 0
                has_requirements = False

                for call in calls_for_intent:
                    decisions = call[0] or []
                    actions = call[1] or []
                    topics = call[2] or []
                    summary = (call[3] or "").lower()

                    if isinstance(decisions, list):
                        total_decisions += len(decisions)
                    if isinstance(actions, list):
                        total_actions += len(actions)

                    # Check for strong intent keywords in summary
                    intent_keywords = ["replacement", "replace", "migrate", "requirement",
                                       "budget", "timeline", "poc", "trial", "evaluate",
                                       "shortlist", "decision"]
                    if any(kw in summary for kw in intent_keywords):
                        has_requirements = True

                if total_decisions > 0:
                    intent_score += 0.3
                    intent_signals.append(f"{total_decisions} decisions recorded")
                if total_actions > 0:
                    intent_score += 0.3
                    intent_signals.append(f"{total_actions} action items")
                if has_requirements:
                    intent_score += 0.4
                    intent_signals.append("buyer intent keywords detected (requirements/budget/timeline/POC)")

                intent_score = min(intent_score, 1.0)
                if intent_signals:
                    factors.append(f"Intent: {', '.join(intent_signals)} ({int(intent_score * 100)}%)")
                else:
                    factors.append("Intent: no signals detected (0%)")

            scores["intent"] = intent_score

            # ── Factor 4: Sentiment (15%) ──
            sentiment_score = 0.5  # neutral default
            if search_term and len(search_term) >= 3:
                sentiments = db.execute(text("""
                    SELECT sentiment, sentiment_score
                    FROM call_insights
                    WHERE (LOWER(summary) LIKE :search
                       OR LOWER(CAST(key_topics AS text)) LIKE :search)
                      AND sentiment IS NOT NULL
                    ORDER BY processed_at DESC LIMIT 5
                """), {"search": f"%{search_term}%"}).fetchall()

                if sentiments:
                    pos = sum(1 for s in sentiments if s[0] == "positive")
                    neg = sum(1 for s in sentiments if s[0] == "negative")
                    total = len(sentiments)

                    if pos > neg:
                        sentiment_score = 0.7 + (0.3 * pos / total)
                        factors.append(f"Sentiment: {pos}/{total} positive calls ({int(sentiment_score * 100)}%)")
                    elif neg > pos:
                        sentiment_score = 0.3 - (0.2 * neg / total)
                        sentiment_score = max(sentiment_score, 0.05)
                        factors.append(f"Sentiment: {neg}/{total} negative calls ({int(sentiment_score * 100)}%)")
                    else:
                        sentiment_score = 0.5
                        factors.append(f"Sentiment: mixed ({total} calls)")
                else:
                    factors.append("Sentiment: no call data (neutral 50%)")

            scores["sentiment"] = sentiment_score

            # ── Factor 5: Deal Velocity (15%) ──
            velocity_score = 0.5  # default
            if created:
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                age_days = (now - created).days

                # Expected days per stage (healthy pace)
                stage_expected_days = {
                    "appointmentscheduled": 30,
                    "presentationscheduled": 45,
                    "decisionmakerboughtin": 60,
                    "1166515347": 75,
                    "219679027": 90,
                    "1157536395": 100,
                    "contractsent": 110,
                }
                expected = stage_expected_days.get(stage, 60)

                if age_days <= expected * 0.5:
                    velocity_score = 0.9
                    factors.append(f"Velocity: {age_days} days (fast, well ahead of {expected}d benchmark)")
                elif age_days <= expected:
                    velocity_score = 0.7
                    factors.append(f"Velocity: {age_days} days (on track, within {expected}d benchmark)")
                elif age_days <= expected * 1.5:
                    velocity_score = 0.4
                    factors.append(f"Velocity: {age_days} days (slowing, past {expected}d benchmark)")
                else:
                    velocity_score = 0.15
                    factors.append(f"Velocity: {age_days} days (stalled, 1.5x past {expected}d benchmark)")

            scores["velocity"] = velocity_score

            # ── Weighted Composite ──
            WEIGHTS = {
                "stage": 0.25,
                "engagement": 0.25,
                "intent": 0.20,
                "sentiment": 0.15,
                "velocity": 0.15,
            }
            composite = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
            composite = round(min(max(composite, 0.02), 0.95), 2)

            # Factor breakdown for transparency
            breakdown = " | ".join(f"{k}={int(scores[k]*100)}%" for k in WEIGHTS)
            factors.append(f"Composite: {breakdown}")

            probabilities.append({
                "deal_name": name,
                "stage": stage,
                "probability": composite,
                "amount": amount,
                "company_name": company,
                "factors": factors,
                "factor_scores": scores,
            })

        logger.info(f"[PreSales] Computed probability for {len(probabilities)} open deals")
        return probabilities

    # ── Pipeline Stages ────────────────────────────────────────────────

    def perceive(self, task: dict) -> dict:
        db = self._current_db
        if not db:
            raise ValueError("No database session available")

        # Run deterministic metrics
        funnel_metrics = self._compute_conversion_rates(db)
        stalled_deals = self._find_stalled_deals(db)
        blockers = self._analyze_blockers(db)

        # If task has a specific deal, compute its probability
        deal_name = task.get("payload", {}).get("deal_name")
        probabilities = self._compute_deal_probability(db, deal_name=deal_name)

        # Store in working memory
        self.memory.set_context("funnel_metrics", funnel_metrics)
        self.memory.set_context("stalled_deals", stalled_deals)
        self.memory.set_context("blockers", blockers)
        self.memory.set_context("probabilities", probabilities)

        logger.info(
            f"[PreSales] Pipeline analysis: {funnel_metrics['total_deals']} deals, "
            f"win_rate={funnel_metrics['overall_win_rate']}, "
            f"{len(stalled_deals)} stalled"
        )
        return task

    def retrieve(self, task: dict) -> dict:
        context = self.memory.assemble_context("pre-sales pipeline analysis")
        context["customer_memory"] = task.get("customer_memory", {})
        return context

    def think(self, task: dict, context: dict) -> dict:
        funnel_metrics = self.memory.get_context("funnel_metrics") or {}
        stalled_deals = self.memory.get_context("stalled_deals") or []
        blockers = self.memory.get_context("blockers") or []
        probabilities = self.memory.get_context("probabilities") or []

        user_message = self._build_prompt(
            funnel_metrics=funnel_metrics,
            stalled_deals=stalled_deals,
            blockers=blockers,
            probabilities=probabilities,
            customer_memory=context.get("customer_memory", {}),
        )

        trait_ctx = task.get("_trait_context", "")
        if trait_ctx:
            user_message += f"\n\n## Agent Guidance\n{trait_ctx}"

        user_message = self._prepend_brief(user_message, task)
        response = self._call_claude(user_message, max_tokens=2048, temperature=0.2)
        return self._parse_claude(response)

    def act(self, task: dict, thinking: dict) -> dict:
        if "error" in thinking:
            return {"success": False, **thinking}

        funnel_metrics = self.memory.get_context("funnel_metrics") or {}
        stalled_deals = self.memory.get_context("stalled_deals") or []
        blockers = self.memory.get_context("blockers") or []
        probabilities = self.memory.get_context("probabilities") or []

        return {
            "success": True,
            "funnel_metrics": funnel_metrics,
            "stalled_deals": stalled_deals[:10],
            "top_blockers": blockers,
            "deal_probabilities": probabilities,
            "summary": thinking.get("summary", "Pipeline analysis complete."),
            "recommendations": thinking.get("recommendations", []),
            "reasoning_summary": thinking.get("summary", "Pipeline analysis complete."),
        }

    # ── Prompt Building ────────────────────────────────────────────────

    def _build_prompt(
        self,
        funnel_metrics: dict,
        stalled_deals: list,
        blockers: list,
        probabilities: list,
        customer_memory: dict,
    ) -> str:
        parts = [
            "## Pre-Sales Pipeline Analysis",
            "",
            "## Funnel Metrics",
            f"Total Deals: {funnel_metrics.get('total_deals', 0)}",
            f"Open Deals: {funnel_metrics.get('open_deals', 0)}",
            f"Closed Won: {funnel_metrics.get('closed_won', 0)}",
            f"Closed Lost: {funnel_metrics.get('closed_lost', 0)}",
            f"Overall Win Rate: {funnel_metrics.get('overall_win_rate', 0):.1%}",
            "",
            "## Stage-to-Stage Conversion",
            f"Discovery -> Demo: {funnel_metrics.get('discovery_to_demo', 0):.1%}",
            f"Demo -> POC: {funnel_metrics.get('demo_to_poc', 0):.1%}",
            f"POC -> Close: {funnel_metrics.get('poc_to_close', 0):.1%}",
        ]

        # Stage distribution
        dist = funnel_metrics.get("stage_distribution", {})
        if dist:
            parts.extend(["", "## Stage Distribution"])
            for stage, count in sorted(dist.items(), key=lambda x: -x[1]):
                parts.append(f"- {stage}: {count} deals")

        # Stalled deals
        if stalled_deals:
            parts.extend(["", f"## Stalled Deals ({len(stalled_deals)} stuck >30 days)"])
            for d in stalled_deals[:10]:
                amt = f"${d['amount']:,.0f}" if d.get("amount") else "N/A"
                parts.append(
                    f"- {d['deal_name']} ({d['company_name'] or 'Unknown'}) — "
                    f"stage: {d['stage']}, stalled {d['days_stalled']} days, value: {amt}"
                )

        # Blockers
        if blockers:
            parts.extend(["", "## Where Deals Die (Closed Lost Analysis)"])
            for b in blockers:
                val = f"${b['total_value']:,.0f}" if b.get("total_value") else "$0"
                parts.append(f"- Stage '{b['stage']}': {b['lost_count']} lost, total value: {val}")

        # Deal probabilities
        if probabilities:
            parts.extend(["", "## Deal Win Probabilities (Open Deals)"])
            for p in probabilities[:10]:
                amt = f"${p['amount']:,.0f}" if p.get("amount") else "N/A"
                parts.append(
                    f"- {p['deal_name']} ({p['company_name'] or 'Unknown'}): "
                    f"{p['probability']:.0%} probability, value: {amt}"
                )
                for f in p.get("factors", []):
                    parts.append(f"  - {f}")

        parts.extend([
            "",
            "## Required Output Format",
            "Return a JSON object with these fields:",
            '- summary: 3-5 sentence narrative of the pipeline health, highlighting '
            'the biggest conversion gaps and risks',
            '- recommendations: array of 3-5 specific actionable recommendations '
            'for the CS team to improve conversion rates and unstall deals',
            '- reasoning: brief explanation of your analysis approach',
        ])

        return "\n".join(parts)


AgentFactory.register("presales_funnel", PreSalesFunnelAgent)
