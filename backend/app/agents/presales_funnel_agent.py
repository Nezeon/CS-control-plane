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
# Contract Sent = order placed, contract being signed. Same level as Closed Won — NOT a regression.
STAGE_ORDER["closedwon"] = STAGE_ORDER["contractsent"]
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
            # Use first word, but prefer longer keys to avoid false matches
            # (e.g., "Union Bank" -> "union" would match "Credit Union")
            words = company.lower().split()
            search_key = words[0]
            if len(search_key) < 5 and len(words) > 1:
                search_key = " ".join(words[:2])  # Use first two words for short names
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
            "contractsent": 0.95, # Contract Sent = order placed, effectively closed
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

            # ── Fetch call insights ONCE for factors 2/3/4 ──
            raw_search = (company or name or "").lower().strip()
            search_term = raw_search.split()[0] if raw_search else ""
            if search_term in ("the", "a", "an", "new", "test"):
                search_term = raw_search
            calls = []
            if search_term and len(search_term) >= 3:
                calls = db.execute(text("""
                    SELECT summary, sentiment, sentiment_score, participants,
                           decisions, action_items, key_topics
                    FROM call_insights
                    WHERE LOWER(summary) LIKE :search
                       OR LOWER(CAST(key_topics AS text)) LIKE :search
                    ORDER BY processed_at DESC LIMIT 5
                """), {"search": f"%{search_term}%"}).fetchall()

            # ── Factor 2: Meeting Engagement (25%) ──
            engagement_score = 0.0
            if calls:
                call_count = len(calls)
                total_participants = 0
                for call in calls:
                    participants = call[3] or []
                    if isinstance(participants, list):
                        total_participants += len(participants)

                if call_count >= 3:
                    engagement_score = 0.9
                elif call_count >= 2:
                    engagement_score = 0.7
                else:
                    engagement_score = 0.5

                avg_participants = total_participants / call_count if call_count else 0
                if avg_participants >= 5:
                    engagement_score = min(engagement_score + 0.1, 1.0)

                factors.append(f"Meetings: {call_count} calls, avg {avg_participants:.0f} participants ({int(engagement_score * 100)}% engagement)")
            else:
                factors.append("Meetings: none found (0% engagement)")
            scores["engagement"] = engagement_score

            # ── Factor 3: Buyer Intent Signals (20%) ──
            intent_score = 0.0
            intent_signals = []
            total_decisions = 0
            total_actions = 0
            has_requirements = False

            for call in calls:
                decisions = call[4] or []
                actions = call[5] or []
                summary_text = (call[0] or "").lower()

                if isinstance(decisions, list):
                    total_decisions += len(decisions)
                if isinstance(actions, list):
                    total_actions += len(actions)

                intent_keywords = ["replacement", "replace", "migrate", "requirement",
                                   "budget", "timeline", "poc", "trial", "evaluate",
                                   "shortlist", "decision"]
                if any(kw in summary_text for kw in intent_keywords):
                    has_requirements = True

            if total_decisions > 0:
                intent_score += 0.3
                intent_signals.append(f"{total_decisions} decisions recorded")
            if total_actions > 0:
                intent_score += 0.3
                intent_signals.append(f"{total_actions} action items")
            if has_requirements:
                intent_score += 0.4
                intent_signals.append("buyer intent keywords detected")
            intent_score = min(intent_score, 1.0)

            if intent_signals:
                factors.append(f"Intent: {', '.join(intent_signals)} ({int(intent_score * 100)}%)")
            elif calls:
                factors.append("Intent: no strong signals (0%)")
            else:
                factors.append("Intent: no call data (0%)")
            scores["intent"] = intent_score

            # ── Factor 4: Sentiment (15%) ──
            sentiment_score = 0.5
            calls_with_sentiment = [c for c in calls if c[1] is not None]
            if calls_with_sentiment:
                pos = sum(1 for c in calls_with_sentiment if c[1] == "positive")
                neg = sum(1 for c in calls_with_sentiment if c[1] == "negative")
                total = len(calls_with_sentiment)

                if pos > neg:
                    sentiment_score = 0.7 + (0.3 * pos / total)
                    factors.append(f"Sentiment: {pos}/{total} positive calls ({int(sentiment_score * 100)}%)")
                elif neg > pos:
                    sentiment_score = max(0.3 - (0.2 * neg / total), 0.05)
                    factors.append(f"Sentiment: {neg}/{total} negative calls ({int(sentiment_score * 100)}%)")
                else:
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

        payload = task.get("payload", {})
        deal_name = payload.get("deal_name", "")
        old_stage = payload.get("old_stage", "")
        new_stage = payload.get("new_stage", "")
        company_name = payload.get("company_name", "")
        deal_id = payload.get("deal_id", "")

        # Compute probability for THIS deal only
        probabilities = self._compute_deal_probability(db, deal_name=deal_name)
        deal_prob = probabilities[0] if probabilities else {}

        deal_data = {
            **deal_prob,
            "old_stage": old_stage,
            "new_stage": new_stage,
            "deal_id": deal_prob.get("deal_id") or deal_id,
            # Fallbacks if _compute_deal_probability didn't match
            "deal_name": deal_prob.get("deal_name") or deal_name,
            "company_name": deal_prob.get("company_name") or company_name,
        }

        self.memory.set_context("deal_data", deal_data)

        logger.info(
            f"[PreSales] Deal analysis: {deal_data['deal_name']} "
            f"({old_stage} -> {new_stage}), "
            f"probability={deal_data.get('probability', 'N/A')}"
        )
        return task

    def retrieve(self, task: dict) -> dict:
        context = self.memory.assemble_context("pre-sales pipeline analysis")
        context["customer_memory"] = task.get("customer_memory", {})
        return context

    def think(self, task: dict, context: dict) -> dict:
        deal_data = self.memory.get_context("deal_data") or {}

        user_message = self._build_prompt(
            deal_data=deal_data,
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

        deal_data = self.memory.get_context("deal_data") or {}

        return {
            "success": True,
            "deal_name": deal_data.get("deal_name", "Unknown"),
            "company_name": deal_data.get("company_name", "Unknown"),
            "deal_id": deal_data.get("deal_id", ""),
            "amount": deal_data.get("amount"),
            "old_stage": deal_data.get("old_stage", ""),
            "new_stage": deal_data.get("new_stage", ""),
            "probability": deal_data.get("probability"),
            "factor_scores": deal_data.get("factor_scores", {}),
            "factors": deal_data.get("factors", []),
            "summary": thinking.get("summary", "Deal analysis complete."),
            "risks": thinking.get("risks", []),
            "next_steps": thinking.get("next_steps", []),
            "reasoning_summary": thinking.get("summary", "Deal analysis complete."),
        }

    # ── Prompt Building ────────────────────────────────────────────────

    def _build_prompt(self, deal_data: dict, customer_memory: dict) -> str:
        deal_name = deal_data.get("deal_name", "Unknown")
        company = deal_data.get("company_name", "Unknown")
        amount = deal_data.get("amount")
        old_stage = deal_data.get("old_stage", "")
        new_stage = deal_data.get("new_stage", "")
        probability = deal_data.get("probability")
        factor_scores = deal_data.get("factor_scores", {})
        factors = deal_data.get("factors", [])

        amt_str = f"${amount:,.0f}" if amount else "N/A"
        prob_str = f"{probability:.0%}" if probability is not None else "N/A"

        parts = [
            "## Deal Stage Change Analysis",
            "",
            f"**Deal:** {deal_name}",
            f"**Company:** {company}",
            f"**Value:** {amt_str}",
            f"**Stage Transition:** {old_stage} -> {new_stage}",
            f"**Win Probability:** {prob_str}",
        ]

        if factor_scores:
            parts.append("")
            parts.append("## Factor Breakdown")
            for k, v in factor_scores.items():
                parts.append(f"- {k.title()}: {int(v * 100)}%")

        if factors:
            parts.append("")
            parts.append("## Factor Details")
            for f in factors:
                parts.append(f"- {f}")

        parts.extend([
            "",
            "## HivePro Pipeline Stage Definitions",
            "- Contract Sent: Order is placed, contract is being signed. This is a POSITIVE terminal stage, equivalent to Closed Won.",
            "- Closed Won ↔ Contract Sent is NOT a regression. It means the contract is being finalized for signature.",
            "- Only movement to Closed Lost or back to an earlier stage (Discovery, Demo, Pre-POC, POC, Negotiation) is a true regression.",
            "",
            "## Required Output Format",
            "Return a JSON object with these fields:",
            "- summary: 2-3 sentence analysis of this deal and what the stage transition means",
            "- risks: array of 1-3 specific risk signals for this deal (empty array if none)",
            "- next_steps: array of 2-4 specific next actions for the sales/CS team",
            "- reasoning: brief explanation of your analysis approach",
        ])

        return "\n".join(parts)


AgentFactory.register("presales_funnel", PreSalesFunnelAgent)
