"""
Alert Rules Engine -- Configurable rules that auto-fire alerts.

Runs as a periodic check (called from health monitor or cron).
Each rule evaluates DB state and creates Alert records when triggered.

Rules 1-5: Original rules (health, tickets, renewals, sentiment) → #cs-health-alerts
Rules 6-9: Escalation rules (stale P0/P1, action items, feature requests,
           recurring complaints) → #cs-executive-urgent
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.alert import Alert

logger = logging.getLogger("services.alert_rules")

# ── Original rules (channel defaults to #cs-health-alerts) ─────────────────

ALERT_RULES = [
    {
        "name": "health_drop_15",
        "title": "Health score dropped >15 points in 7 days",
        "severity": "high",
        "alert_type": "health_decline",
        "query": """
            WITH latest AS (
                SELECT DISTINCT ON (customer_id) customer_id, score
                FROM health_scores ORDER BY customer_id, calculated_at DESC
            ),
            week_ago AS (
                SELECT DISTINCT ON (customer_id) customer_id, score
                FROM health_scores
                WHERE calculated_at <= NOW() - INTERVAL '7 days'
                ORDER BY customer_id, calculated_at DESC
            )
            SELECT c.id AS customer_id, c.name,
                   w.score AS old_score, l.score AS new_score,
                   (w.score - l.score) AS drop_amount
            FROM customers c
            JOIN latest l ON l.customer_id = c.id
            JOIN week_ago w ON w.customer_id = c.id
            WHERE (w.score - l.score) > 15
              AND c.is_active = true
        """,
        "detail_template": "Health dropped from {old_score} to {new_score} ({drop_amount} point decline in 7 days)",
        "action_template": "Schedule an urgent check-in call with {name} to identify root causes",
    },
    {
        "name": "critical_tickets_stale_p0",
        "title": "Critical/P0 ticket open >7 days without resolution",
        "severity": "high",
        "alert_type": "stale_p0_ticket",
        "query": """
            SELECT c.id AS customer_id, c.name,
                   t.summary, t.severity,
                   EXTRACT(DAY FROM NOW() - t.created_at)::int AS days_open
            FROM tickets t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.severity IN ('P0', 'critical')
              AND t.status NOT IN ('resolved', 'closed')
              AND t.created_at < NOW() - INTERVAL '7 days'
              AND c.is_active = true
        """,
        "detail_template": "P0 ticket \"{summary}\" open for {days_open} days",
        "action_template": "Escalate {name}'s P0 ticket immediately — aging beyond threshold",
    },
    {
        "name": "critical_tickets_stale_p1",
        "title": "P1 ticket open >10 days without resolution",
        "severity": "high",
        "alert_type": "stale_p1_ticket",
        "query": """
            SELECT c.id AS customer_id, c.name,
                   t.summary, t.severity,
                   EXTRACT(DAY FROM NOW() - t.created_at)::int AS days_open
            FROM tickets t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.severity = 'P1'
              AND t.status NOT IN ('resolved', 'closed')
              AND t.created_at < NOW() - INTERVAL '10 days'
              AND c.is_active = true
        """,
        "detail_template": "P1 ticket \"{summary}\" open for {days_open} days",
        "action_template": "Escalate {name}'s P1 ticket — aging beyond threshold",
    },
    {
        "name": "renewal_at_risk",
        "title": "At-risk customer with renewal in <60 days",
        "severity": "critical",
        "alert_type": "renewal_risk",
        "query": """
            SELECT c.id AS customer_id, c.name, c.renewal_date, h.score, h.risk_level
            FROM customers c
            LEFT JOIN LATERAL (
                SELECT score, risk_level FROM health_scores
                WHERE customer_id = c.id ORDER BY calculated_at DESC LIMIT 1
            ) h ON true
            WHERE c.renewal_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '60 days'
              AND h.risk_level IN ('high_risk', 'critical', 'high')
              AND c.is_active = true
        """,
        "detail_template": "Renewal on {renewal_date} with health score {score} ({risk_level})",
        "action_template": "Initiate executive sponsor engagement for {name} before renewal",
    },
    {
        "name": "negative_sentiment_streak",
        "title": "3+ consecutive negative sentiment calls",
        "severity": "medium",
        "alert_type": "sentiment_decline",
        "query": """
            WITH ranked AS (
                SELECT ci.customer_id, c.name, ci.sentiment,
                       ROW_NUMBER() OVER (PARTITION BY ci.customer_id ORDER BY ci.processed_at DESC) AS rn
                FROM call_insights ci
                JOIN customers c ON ci.customer_id = c.id
                WHERE ci.sentiment IS NOT NULL
                  AND c.is_active = true
            )
            SELECT customer_id, name, COUNT(*) AS streak
            FROM ranked
            WHERE rn <= 3 AND sentiment IN ('negative', 'mixed')
            GROUP BY customer_id, name
            HAVING COUNT(*) >= 3
        """,
        "detail_template": "Last {streak} calls had negative/mixed sentiment",
        "action_template": "Review recent call recordings for {name} and identify recurring concerns",
    },

    # ── Escalation rules → #cs-executive-urgent ────────────────────────────

    {
        "name": "escalation_stale_p0",
        "title": "P0 escalation stale",
        "severity": "critical",
        "alert_type": "escalation_stale_p0",
        "channel": "exec_urgent",
        "query": f"""
            SELECT c.id AS customer_id, c.name,
                   t.summary, t.severity, t.jira_id,
                   EXTRACT(DAY FROM NOW() - t.created_at)::int AS days_open,
                   c.metadata->>'cs_manager' AS cs_manager
            FROM tickets t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.severity IN ('P0', 'critical')
              AND t.status NOT IN ('resolved', 'closed')
              AND t.created_at < NOW() - INTERVAL '{settings.ESCALATION_STALE_P0_DAYS} days'
              AND c.is_active = true
        """,
        "detail_template": "P0 ticket \"{summary}\" ({jira_id}) open {days_open} days (threshold: {threshold}d). CS Manager: {cs_manager}",
        "action_template": "Follow up immediately — {name}'s P0 ticket is past the {threshold}-day SLA",
    },
    {
        "name": "escalation_stale_p1",
        "title": "P1 escalation stale",
        "severity": "high",
        "alert_type": "escalation_stale_p1",
        "channel": "exec_urgent",
        "query": f"""
            SELECT c.id AS customer_id, c.name,
                   t.summary, t.severity, t.jira_id,
                   EXTRACT(DAY FROM NOW() - t.created_at)::int AS days_open,
                   c.metadata->>'cs_manager' AS cs_manager
            FROM tickets t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.severity = 'P1'
              AND t.status NOT IN ('resolved', 'closed')
              AND t.created_at < NOW() - INTERVAL '{settings.ESCALATION_STALE_P1_DAYS} days'
              AND c.is_active = true
        """,
        "detail_template": "P1 ticket \"{summary}\" ({jira_id}) open {days_open} days (threshold: {threshold}d). CS Manager: {cs_manager}",
        "action_template": "Escalate {name}'s P1 ticket to engineering — aging past {threshold}-day threshold",
    },
]


class AlertRulesEngine:
    """Evaluates alert rules against DB state and creates alerts."""

    def evaluate_all(self, db: Session) -> dict:
        """Run all rules and create alerts for any triggers."""
        return self._run_rules(db, ALERT_RULES)

    def evaluate_by_names(self, db: Session, rule_names: list[str]) -> dict:
        """Run only the specified rules by name."""
        rules = [r for r in ALERT_RULES if r["name"] in rule_names]
        stats = self._run_rules(db, rules)

        # Also run custom (non-SQL) rules if requested
        if "unanswered_action_items" in rule_names:
            custom = self._evaluate_unanswered_actions(db)
            stats["alerts_created"] += len(custom)
            stats["rules_checked"] += 1
            stats["details"].extend(custom)

        if "repeated_feature_requests" in rule_names:
            custom = self._evaluate_repeated_features(db)
            stats["alerts_created"] += len(custom)
            stats["rules_checked"] += 1
            stats["details"].extend(custom)

        if "recurring_complaints" in rule_names:
            custom = self._evaluate_recurring_complaints(db)
            stats["alerts_created"] += len(custom)
            stats["rules_checked"] += 1
            stats["details"].extend(custom)

        db.commit()
        return stats

    def _run_rules(self, db: Session, rules: list[dict]) -> dict:
        """Core loop: evaluate a list of SQL-based rules."""
        stats = {"rules_checked": 0, "alerts_created": 0, "details": []}

        for rule in rules:
            stats["rules_checked"] += 1
            try:
                created = self._evaluate_rule(db, rule)
                stats["alerts_created"] += len(created)
                stats["details"].extend(created)
            except Exception as e:
                logger.error(f"[AlertRules] Rule '{rule['name']}' failed: {e}")

        db.commit()
        logger.info(
            f"[AlertRules] Checked {stats['rules_checked']} rules, "
            f"created {stats['alerts_created']} alerts"
        )
        return stats

    def _resolve_channel(self, rule: dict) -> str | None:
        """Resolve channel key to actual Slack channel ID/name."""
        ch = rule.get("channel")
        if ch == "exec_urgent":
            return settings.SLACK_CH_EXEC_URGENT
        return None  # Default — send_alert will use #cs-health-alerts

    def _evaluate_rule(self, db: Session, rule: dict) -> list:
        """Evaluate a single SQL-based rule and create alerts for matching rows."""
        rows = db.execute(text(rule["query"])).fetchall()
        created = []
        channel = self._resolve_channel(rule)

        for row in rows:
            row_dict = dict(row._mapping)
            customer_id = row_dict["customer_id"]
            name = row_dict["name"]

            # Inject threshold into template context for escalation rules
            if "escalation_stale_p0" in rule["name"]:
                row_dict["threshold"] = settings.ESCALATION_STALE_P0_DAYS
            elif "escalation_stale_p1" in rule["name"]:
                row_dict["threshold"] = settings.ESCALATION_STALE_P1_DAYS
            # Fill missing cs_manager
            row_dict.setdefault("cs_manager", "unassigned")

            # Skip if an identical alert already exists and is open
            existing = (
                db.query(Alert)
                .filter_by(
                    customer_id=customer_id,
                    alert_type=rule["alert_type"],
                    status="open",
                )
                .first()
            )
            if existing:
                continue

            detail = rule["detail_template"].format(**row_dict)
            action = rule["action_template"].format(**row_dict)

            alert = Alert(
                id=uuid.uuid4(),
                customer_id=customer_id,
                alert_type=rule["alert_type"],
                severity=rule["severity"],
                title=f"{rule['title']} — {name}",
                description=detail,
                suggested_action=action,
                status="open",
            )
            db.add(alert)

            try:
                from app.services.slack_service import slack_service
                if slack_service.configured:
                    db.flush()
                    db.refresh(alert)
                    sent = slack_service.send_alert(alert, channel=channel)
                    if sent:
                        alert.slack_notified = True
            except Exception:
                pass

            created.append({
                "rule": rule["name"],
                "customer": name,
                "title": alert.title,
            })

        return created

    # ── Rule 4: Unanswered Action Items (fire-once per action item) ────────

    def _evaluate_unanswered_actions(self, db: Session) -> list:
        """
        Fire-once alert for action items pending >N days with no follow-up.
        Dedup key: action_item ID stored in alert.similar_past_issues JSONB.
        """
        days = settings.ESCALATION_ACTION_FOLLOWUP_DAYS
        channel = settings.SLACK_CH_EXEC_URGENT

        rows = db.execute(text("""
            SELECT ai.id AS action_id, ai.title AS action_title,
                   ai.created_at AS action_created,
                   c.id AS customer_id, c.name,
                   c.metadata->>'cs_manager' AS cs_manager,
                   ci.summary AS call_title
            FROM action_items ai
            JOIN customers c ON ai.customer_id = c.id
            LEFT JOIN call_insights ci ON ci.id = ai.source_id
            WHERE ai.status NOT IN ('completed', 'dismissed')
              AND ai.created_at < NOW() - INTERVAL :days
              AND c.is_active = true
        """), {"days": f"{days} days"}).fetchall()

        created = []
        for r in rows:
            row = dict(r._mapping)
            action_id = str(row["action_id"])

            # Fire-once: check if we already alerted for THIS specific action item
            existing = (
                db.query(Alert)
                .filter(
                    Alert.alert_type == "unanswered_action_item",
                    Alert.similar_past_issues.contains([{"action_item_id": action_id}]),
                )
                .first()
            )
            if existing:
                continue

            days_old = (datetime.now(timezone.utc) - row["action_created"].replace(tzinfo=timezone.utc)).days
            cs_mgr = row["cs_manager"] or "unassigned"
            call = row["call_title"] or "unknown call"

            alert = Alert(
                id=uuid.uuid4(),
                customer_id=row["customer_id"],
                alert_type="unanswered_action_item",
                severity="medium",
                title=f"Unanswered action item — {row['name']}",
                description=(
                    f"Action item \"{row['action_title']}\" from call \"{call}\" "
                    f"has been pending for {days_old} days (threshold: {days}d). "
                    f"CS Manager: {cs_mgr}"
                ),
                suggested_action=f"Follow up on the pending action item for {row['name']}",
                status="open",
                similar_past_issues=[{"action_item_id": action_id}],
            )
            db.add(alert)

            try:
                from app.services.slack_service import slack_service
                if slack_service.configured:
                    db.flush()
                    db.refresh(alert)
                    slack_service.send_alert(alert, channel=channel)
                    alert.slack_notified = True
            except Exception:
                pass

            created.append({
                "rule": "unanswered_action_items",
                "customer": row["name"],
                "title": alert.title,
            })

        logger.info(f"[AlertRules] Unanswered action items: {len(created)} alerts created")
        return created

    # ── Rules 1 & 2: AI-grouped feature requests + recurring complaints ────

    def _evaluate_repeated_features(self, db: Session) -> list:
        """
        Use Claude to group similar feature request tickets, then alert if
        3+ distinct customers requested the same thing in the last N days.
        """
        window = settings.ESCALATION_PATTERN_WINDOW_DAYS
        min_customers = settings.ESCALATION_FEATURE_MIN_CUSTOMERS

        rows = db.execute(text("""
            SELECT t.id, t.summary, t.jira_id, c.id AS customer_id, c.name
            FROM tickets t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.ticket_type IN ('New Feature', 'Improvement')
              AND t.created_at >= NOW() - INTERVAL :window
              AND c.is_active = true
            ORDER BY t.created_at DESC
        """), {"window": f"{window} days"}).fetchall()

        if len(rows) < min_customers:
            return []

        return self._ai_group_and_alert(
            db, rows,
            alert_type="repeated_feature_request",
            min_count=min_customers,
            count_distinct_customers=True,
            severity="high",
            title_prefix="Trending feature request",
            action_prefix="Review for roadmap prioritization",
        )

    def _evaluate_recurring_complaints(self, db: Session) -> list:
        """
        Use Claude to group similar complaint/bug tickets, then alert if
        3+ occurrences of the same issue in the last N days.
        """
        window = settings.ESCALATION_PATTERN_WINDOW_DAYS
        min_occurrences = settings.ESCALATION_RECURRING_MIN_OCCURRENCES

        rows = db.execute(text("""
            SELECT t.id, t.summary, t.jira_id, c.id AS customer_id, c.name
            FROM tickets t
            JOIN customers c ON t.customer_id = c.id
            WHERE t.ticket_type IN ('Bug', 'Task')
              AND t.created_at >= NOW() - INTERVAL :window
              AND c.is_active = true
            ORDER BY t.created_at DESC
        """), {"window": f"{window} days"}).fetchall()

        if len(rows) < min_occurrences:
            return []

        return self._ai_group_and_alert(
            db, rows,
            alert_type="recurring_complaint",
            min_count=min_occurrences,
            count_distinct_customers=False,
            severity="high",
            title_prefix="Recurring issue detected",
            action_prefix="Escalate to engineering — systemic issue",
        )

    def _ai_group_and_alert(
        self, db: Session, rows, *,
        alert_type: str, min_count: int, count_distinct_customers: bool,
        severity: str, title_prefix: str, action_prefix: str,
    ) -> list:
        """
        Send ticket summaries to Claude for semantic grouping, then create
        alerts for groups that meet the threshold.
        """
        from app.services.claude_service import ClaudeService
        claude = ClaudeService()
        channel = settings.SLACK_CH_EXEC_URGENT

        # Build context for Claude
        ticket_lines = []
        for r in rows:
            ticket_lines.append(f"ID:{r.id} | Customer:{r.name} | Jira:{r.jira_id} | \"{r.summary}\"")

        if not ticket_lines:
            return []

        system = (
            "You are a support ticket analyst. Group the following tickets by similar topic/issue. "
            "Return ONLY valid JSON: an array of groups. Each group is an object with:\n"
            "  - \"topic\": short description of the shared issue (under 60 chars)\n"
            "  - \"ticket_ids\": array of the ID values that belong to this group\n"
            "Tickets that don't match any group should be in a group with topic \"Other\".\n"
            "Be aggressive about grouping — tickets about the same underlying issue should be together."
        )
        user_msg = "\n".join(ticket_lines)

        result = claude.generate_fast_sync(
            system_prompt=system,
            user_message=user_msg,
            max_tokens=1000,
            temperature=0.1,
        )

        if result.get("error"):
            logger.warning(f"[AlertRules] AI grouping failed: {result['error']}")
            return []

        # Parse Claude's JSON response
        import json
        try:
            content = result["content"].strip()
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            groups = json.loads(content)
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.warning(f"[AlertRules] Failed to parse AI grouping response: {e}")
            return []

        # Build lookup: ticket_id -> row data
        row_map = {str(r.id): r for r in rows}

        created = []
        for group in groups:
            topic = group.get("topic", "Unknown")
            if topic == "Other":
                continue

            ticket_ids = [str(tid) for tid in group.get("ticket_ids", [])]
            matched_rows = [row_map[tid] for tid in ticket_ids if tid in row_map]

            if not matched_rows:
                continue

            if count_distinct_customers:
                count = len(set(r.customer_id for r in matched_rows))
            else:
                count = len(matched_rows)

            if count < min_count:
                continue

            # Dedup: don't re-alert for the same topic if one is already open
            existing = (
                db.query(Alert)
                .filter(
                    Alert.alert_type == alert_type,
                    Alert.status == "open",
                    Alert.description.ilike(f"%{topic[:30]}%"),
                )
                .first()
            )
            if existing:
                continue

            customer_names = sorted(set(r.name for r in matched_rows))
            jira_ids = [r.jira_id for r in matched_rows if r.jira_id]
            # Use first customer for the alert FK (the alert is cross-customer)
            primary_customer_id = matched_rows[0].customer_id

            detail = (
                f"Topic: \"{topic}\" ({count} {'customers' if count_distinct_customers else 'tickets'} "
                f"in {settings.ESCALATION_PATTERN_WINDOW_DAYS} days)\n"
                f"Affected: {', '.join(customer_names[:5])}\n"
                f"Tickets: {', '.join(jira_ids[:5])}"
            )

            alert = Alert(
                id=uuid.uuid4(),
                customer_id=primary_customer_id,
                alert_type=alert_type,
                severity=severity,
                title=f"{title_prefix} — {topic}",
                description=detail,
                suggested_action=f"{action_prefix}: {topic}",
                status="open",
                similar_past_issues=[{"topic": topic, "ticket_count": count}],
            )
            db.add(alert)

            try:
                from app.services.slack_service import slack_service
                if slack_service.configured:
                    db.flush()
                    db.refresh(alert)
                    slack_service.send_alert(alert, channel=channel)
                    alert.slack_notified = True
            except Exception:
                pass

            created.append({
                "rule": alert_type,
                "customer": ", ".join(customer_names[:3]),
                "title": alert.title,
            })

        logger.info(f"[AlertRules] {alert_type}: {len(created)} alerts created from AI grouping")
        return created


alert_rules_engine = AlertRulesEngine()
