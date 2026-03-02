"""
Seed script for CS Control Plane.

Usage: cd backend && python -m app.utils.seed

Creates:
- 5 users
- 10 customers
- 300 health scores (30 days x 10 customers)
- Action items for at-risk customers
- 50 tickets (5 per customer, ~30% with troubleshoot_result)
- 100 call insights (10 per customer)
- 200 agent logs (all 9 agents)
- 50 events (all 11 event types)
- 15 alerts
- 8 reports (3 weekly_digest, 3 monthly_report, 2 qbr)
- ChromaDB embeddings for tickets and insights
"""

import random
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.action_item import ActionItem
from app.models.agent_log import AgentLog
from app.models.alert import Alert
from app.models.call_insight import CallInsight
from app.models.customer import Customer
from app.models.event import Event
from app.models.health_score import HealthScore
from app.models.report import Report
from app.models.ticket import Ticket
from app.models.user import User
from app.utils.security import hash_password

engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)

# Factor max weights (must sum to 100)
FACTOR_MAXES = {
    "ticket_severity": 20,
    "sla_compliance": 20,
    "sentiment": 15,
    "engagement": 15,
    "deployment_health": 15,
    "resolution_rate": 15,
}

USERS = [
    {"email": "ayushmaan@hivepro.com", "full_name": "Ayushmaan Naruka", "role": "admin"},
    {"email": "ariza@hivepro.com", "full_name": "Ariza Zehra", "role": "admin"},
    {"email": "vignesh@hivepro.com", "full_name": "Vignesh", "role": "cs_engineer"},
    {"email": "chaitanya@hivepro.com", "full_name": "Chaitanya", "role": "cs_engineer"},
    {"email": "kazi@hivepro.com", "full_name": "Kazi", "role": "cs_manager"},
]

CUSTOMERS = [
    {
        "name": "Acme Corp",
        "industry": "Banking",
        "tier": "enterprise",
        "cs_owner_email": "vignesh@hivepro.com",
        "target_health": 42,
        "deployment_mode": "OVA",
        "product_version": "4.2.1",
        "integrations": ["Qualys", "CrowdStrike", "ServiceNow"],
        "known_constraints": ["EDR installed", "Air-gapped network"],
        "primary_contact_name": "John Doe",
        "primary_contact_email": "john.doe@acme.com",
    },
    {
        "name": "Beta Financial",
        "industry": "Finance",
        "tier": "enterprise",
        "cs_owner_email": "vignesh@hivepro.com",
        "target_health": 78,
        "deployment_mode": "Cloud",
        "product_version": "4.3.0",
        "integrations": ["Qualys", "ServiceNow", "Splunk"],
        "known_constraints": [],
        "primary_contact_name": "Sarah Chen",
        "primary_contact_email": "sarah.chen@betafin.com",
    },
    {
        "name": "Gamma Telecom",
        "industry": "Telecom",
        "tier": "enterprise",
        "cs_owner_email": "chaitanya@hivepro.com",
        "target_health": 55,
        "deployment_mode": "Hybrid",
        "product_version": "4.2.0",
        "integrations": ["CrowdStrike", "Jira"],
        "known_constraints": ["No root access", "Multiple VLANs"],
        "primary_contact_name": "Raj Patel",
        "primary_contact_email": "raj.patel@gammatelecom.com",
    },
    {
        "name": "Delta Health",
        "industry": "Healthcare",
        "tier": "mid_market",
        "cs_owner_email": "chaitanya@hivepro.com",
        "target_health": 91,
        "deployment_mode": "Cloud",
        "product_version": "4.3.0",
        "integrations": ["Qualys", "ServiceNow"],
        "known_constraints": ["HIPAA compliance"],
        "primary_contact_name": "Dr. Emily Roberts",
        "primary_contact_email": "e.roberts@deltahealth.org",
    },
    {
        "name": "Epsilon Insurance",
        "industry": "Insurance",
        "tier": "enterprise",
        "cs_owner_email": "vignesh@hivepro.com",
        "target_health": 38,
        "deployment_mode": "OVA",
        "product_version": "4.1.5",
        "integrations": ["Qualys"],
        "known_constraints": ["Legacy infrastructure", "No EDR"],
        "primary_contact_name": "Mark Thompson",
        "primary_contact_email": "m.thompson@epsilon-ins.com",
    },
    {
        "name": "Zeta Retail",
        "industry": "Retail",
        "tier": "mid_market",
        "cs_owner_email": "chaitanya@hivepro.com",
        "target_health": 67,
        "deployment_mode": "Cloud",
        "product_version": "4.2.1",
        "integrations": ["CrowdStrike", "Slack"],
        "known_constraints": [],
        "primary_contact_name": "Lisa Wang",
        "primary_contact_email": "l.wang@zetaretail.com",
    },
    {
        "name": "Eta Pharma",
        "industry": "Pharma",
        "tier": "enterprise",
        "cs_owner_email": "vignesh@hivepro.com",
        "target_health": 85,
        "deployment_mode": "On-Premise",
        "product_version": "4.3.0",
        "integrations": ["Qualys", "CrowdStrike", "ServiceNow", "Splunk"],
        "known_constraints": ["GxP validation required"],
        "primary_contact_name": "Anna Müller",
        "primary_contact_email": "a.muller@etapharma.de",
    },
    {
        "name": "Theta Energy",
        "industry": "Energy",
        "tier": "mid_market",
        "cs_owner_email": "chaitanya@hivepro.com",
        "target_health": 72,
        "deployment_mode": "Hybrid",
        "product_version": "4.2.0",
        "integrations": ["Qualys", "Jira"],
        "known_constraints": ["OT/IT segmentation"],
        "primary_contact_name": "James Wilson",
        "primary_contact_email": "j.wilson@thetaenergy.com",
    },
    {
        "name": "Iota Defense",
        "industry": "Defense",
        "tier": "enterprise",
        "cs_owner_email": "vignesh@hivepro.com",
        "target_health": 44,
        "deployment_mode": "On-Premise",
        "product_version": "4.1.5",
        "integrations": ["CrowdStrike"],
        "known_constraints": ["Air-gapped network", "STIG compliance", "No cloud connectivity"],
        "primary_contact_name": "Col. David Kim",
        "primary_contact_email": "d.kim@iotadefense.gov",
    },
    {
        "name": "Kappa Logistics",
        "industry": "Logistics",
        "tier": "smb",
        "cs_owner_email": "chaitanya@hivepro.com",
        "target_health": 60,
        "deployment_mode": "Cloud",
        "product_version": "4.3.0",
        "integrations": ["Jira"],
        "known_constraints": [],
        "primary_contact_name": "Tom Garcia",
        "primary_contact_email": "t.garcia@kappalog.com",
    },
]

ACTION_ITEM_TEMPLATES = [
    ("Schedule escalation call with engineering", "Customer experiencing repeated scan failures, needs L3 support engagement"),
    ("Review and update deployment configuration", "Current configuration may be contributing to performance issues"),
    ("Prepare risk mitigation plan", "Multiple risk flags detected — need documented remediation steps"),
    ("Follow up on pending support tickets", "Several tickets approaching SLA deadline without resolution"),
    ("Conduct health check review with customer", "Health score declining — proactive outreach needed"),
    ("Update integration settings", "Integration compatibility issues reported after recent update"),
]

TICKET_TEMPLATES = [
    {"type": "scan_failure", "severity": "P1", "summary": "Full network scan failing on subnet {subnet}", "description": "Scan jobs initiated at {time} are failing with timeout errors on subnet {subnet}. The scanner agent reports connection refused on multiple hosts."},
    {"type": "scan_failure", "severity": "P2", "summary": "Partial scan results on {subnet} — missing 30% of assets", "description": "Weekly vulnerability scan returning incomplete results. Approximately 30% of known assets on {subnet} are not being scanned."},
    {"type": "connector_issue", "severity": "P2", "summary": "{connector} connector sync failing since {date}", "description": "The {connector} integration is returning HTTP 401 errors during scheduled sync. Last successful sync was on {date}."},
    {"type": "connector_issue", "severity": "P3", "summary": "{connector} data ingestion delayed by 6+ hours", "description": "Data from {connector} is arriving with significant delay. Expected real-time but seeing 6-12 hour lag."},
    {"type": "deployment", "severity": "P1", "summary": "OVA deployment stuck at 85% — database migration failing", "description": "Attempting to upgrade from {old_ver} to {new_ver}. Deployment hangs at database migration step with schema conflict error."},
    {"type": "deployment", "severity": "P3", "summary": "Post-upgrade validation checks failing for {component}", "description": "After upgrading to {new_ver}, the {component} validation is reporting 3 failed checks related to certificate chain verification."},
    {"type": "configuration", "severity": "P2", "summary": "RBAC permissions not propagating after policy update", "description": "Updated RBAC policy for the security team role, but changes are not reflected for 12+ users. Cache invalidation may be needed."},
    {"type": "configuration", "severity": "P3", "summary": "Custom severity mapping not applied to {connector} findings", "description": "Configured custom severity overrides for {connector} CVEs but original severity values are still shown in dashboard."},
    {"type": "performance", "severity": "P1", "summary": "Dashboard loading time exceeding 30 seconds", "description": "Main dashboard takes 30-45 seconds to load. API response times for /api/vulnerabilities endpoint are 15+ seconds."},
    {"type": "performance", "severity": "P2", "summary": "Report generation timing out for large asset inventories", "description": "Compliance report generation fails with timeout when asset count exceeds 10,000. Worked fine with previous dataset."},
    {"type": "access_control", "severity": "P2", "summary": "SSO login loop after IdP certificate rotation", "description": "After rotating SAML certificates in the IdP, users are stuck in a redirect loop when trying to authenticate via SSO."},
    {"type": "access_control", "severity": "P3", "summary": "API token expiration not matching configured TTL", "description": "API tokens are expiring after 1 hour despite TTL being set to 8 hours. Affecting automated scanning schedules."},
    {"type": "integration", "severity": "P2", "summary": "Webhook delivery to {connector} failing with 503", "description": "Outbound webhooks to {connector} endpoint are receiving 503 responses. {connector} team confirms their endpoint is healthy."},
    {"type": "integration", "severity": "P3", "summary": "Duplicate findings created from {connector} import", "description": "Each {connector} sync is creating duplicate vulnerability findings instead of updating existing ones. Deduplication logic may be broken."},
    {"type": "scan_failure", "severity": "P4", "summary": "Informational: Scan schedule optimization recommendation", "description": "Current scan schedule has 3 overlapping scan windows. Recommend restructuring to improve resource utilization."},
]

CONNECTORS = ["Qualys", "CrowdStrike", "ServiceNow", "Splunk", "Jira", "Tenable"]
SUBNETS = ["10.0.1.0/24", "192.168.1.0/24", "172.16.0.0/16", "10.10.5.0/24", "10.0.100.0/24"]
COMPONENTS = ["scanner-agent", "api-gateway", "report-engine", "data-pipeline", "auth-service"]

INSIGHT_SUMMARIES = [
    "Discussed deployment timeline and upgrade path from {old_ver} to {new_ver}. Customer concerned about downtime window.",
    "Reviewed Q{quarter} scan results and vulnerability trending. Customer pleased with 15% reduction in critical findings.",
    "Customer raised concerns about scan performance after recent network expansion. Agreed to optimize scan windows.",
    "Renewal discussion — customer wants to expand license to cover {count} additional assets across new datacenter.",
    "Escalation review: resolved {count} P1 tickets this month. Customer appreciates quick response times.",
    "Security team demo for new {feature} feature. Customer excited about automated remediation capabilities.",
    "Quarterly business review prep call. Reviewed ROI metrics and customer success milestones.",
    "Troubleshooting session for {connector} integration issues. Root cause identified as API rate limiting.",
    "Onboarding call for new security analyst team members. Walked through dashboard and report workflows.",
    "Customer requesting custom API integration for their SOAR platform. Discussed feasibility and timeline.",
    "Post-incident review after P1 scan failure. Identified network configuration as root cause.",
    "License utilization review — customer using 78% of licensed capacity. Recommended optimization.",
    "Compliance audit preparation call. Reviewed PCI-DSS scan configurations and reporting.",
    "Feature feedback session — customer submitted 5 enhancement requests for next release.",
    "Emergency call: production scanner down after infrastructure change. Guided recovery steps.",
]

INSIGHT_TOPICS = [
    ["deployment", "upgrade", "timeline"],
    ["vulnerability", "scan results", "trending"],
    ["performance", "optimization", "network"],
    ["renewal", "expansion", "licensing"],
    ["escalation", "support", "SLA"],
    ["feature demo", "automation", "remediation"],
    ["QBR", "ROI", "success metrics"],
    ["integration", "troubleshooting", "API"],
    ["onboarding", "training", "workflow"],
    ["custom integration", "API", "SOAR"],
    ["incident review", "root cause", "network"],
    ["license", "utilization", "optimization"],
    ["compliance", "audit", "PCI-DSS"],
    ["feedback", "feature requests", "roadmap"],
    ["emergency", "outage", "recovery"],
]

INSIGHT_DECISIONS = [
    ["Schedule upgrade for next maintenance window", "Create staging environment for testing"],
    ["Continue monthly scan cadence", "Add new subnet to scan scope"],
    ["Optimize scan schedule to off-peak hours", "Increase scanner agent resources"],
    ["Prepare renewal proposal with expansion pricing", "Schedule executive sponsor meeting"],
    ["Maintain current escalation process", "Add weekly sync for open P1s"],
    ["Enable beta feature in staging", "Schedule hands-on workshop"],
    ["Present QBR deck to executive sponsor", "Update success metrics dashboard"],
    ["Implement rate limiting workaround", "Open vendor support ticket"],
    ["Create custom training materials", "Schedule follow-up in 2 weeks"],
    ["Scope API integration project", "Assign dedicated SE resource"],
]

AGENT_NAMES = [
    "health_monitor", "call_intelligence", "ticket_triage", "customer_memory",
    "troubleshooter", "escalation_summary", "qbr_value", "sow_prerequisite", "deployment_intelligence",
]
AGENT_TYPES = {
    "health_monitor": "value", "call_intelligence": "value", "ticket_triage": "support",
    "customer_memory": "control", "troubleshooter": "support", "escalation_summary": "support",
    "qbr_value": "value", "sow_prerequisite": "delivery", "deployment_intelligence": "delivery",
}
EVENT_TYPES = {
    "health_monitor": "daily_health_check",
    "call_intelligence": "fathom_recording_ready",
    "ticket_triage": "jira_ticket_created",
    "customer_memory": "daily_health_check",
    "troubleshooter": "support_bundle_uploaded",
    "escalation_summary": "ticket_escalated",
    "qbr_value": "renewal_approaching",
    "sow_prerequisite": "new_enterprise_customer",
    "deployment_intelligence": "deployment_started",
}

ALERT_TEMPLATES = [
    {"type": "health_score_drop", "severity": "high", "title": "Health score dropped below {threshold} for {customer}", "description": "Customer health score decreased from {old_score} to {new_score} in the last 7 days.", "action": "Schedule immediate review call with CS owner and customer primary contact"},
    {"type": "sla_breach", "severity": "critical", "title": "SLA breach on P1 ticket for {customer}", "description": "Ticket {ticket_id} has exceeded the 4-hour SLA for P1 resolution. Currently at {hours} hours.", "action": "Escalate to engineering lead and notify customer of resolution timeline"},
    {"type": "sentiment_decline", "severity": "medium", "title": "Negative sentiment trend detected for {customer}", "description": "Last 3 calls show declining sentiment scores: {scores}. Key concerns around {topic}.", "action": "Review recent call transcripts and prepare proactive outreach plan"},
    {"type": "engagement_drop", "severity": "medium", "title": "Engagement drop for {customer} — no calls in {days} days", "description": "Customer has not had any scheduled calls in {days} days. Previous cadence was bi-weekly.", "action": "Send re-engagement email and propose a check-in call"},
    {"type": "health_score_drop", "severity": "critical", "title": "Critical health score for {customer}: {new_score}/100", "description": "Health score has been in critical range for 5+ consecutive days. Multiple risk flags active.", "action": "Initiate executive escalation and prepare risk mitigation plan"},
]


def get_risk_level(score: int) -> str:
    if score >= 70:
        return "healthy"
    elif score >= 50:
        return "watch"
    elif score >= 25:
        return "high_risk"
    else:
        return "critical"


def get_risk_flags(score: int, risk_level: str) -> list[str]:
    flags = []
    if risk_level == "critical":
        flags = [
            f"{random.randint(4, 6)} overdue tickets",
            "Negative sentiment trend",
            "SLA breach on P1",
            "No engagement in 14 days",
        ]
    elif risk_level == "high_risk":
        choices = [
            f"{random.randint(2, 4)} overdue tickets",
            "Negative sentiment trend",
            "SLA breach on P1",
            "Deployment scan failures",
            "Declining engagement",
        ]
        flags = random.sample(choices, k=random.randint(2, 3))
    elif risk_level == "watch":
        choices = [
            "Slight sentiment dip",
            "1 approaching SLA deadline",
            "Engagement below average",
            "Minor deployment issues",
        ]
        flags = random.sample(choices, k=random.randint(1, 2))
    return flags


def generate_factors(total_score: int) -> dict:
    """Generate 6 factor scores that approximately sum to total_score."""
    factor_names = list(FACTOR_MAXES.keys())
    max_total = sum(FACTOR_MAXES.values())  # 100

    # Scale each factor proportionally to the total score
    ratio = total_score / max_total
    factors = {}
    running_sum = 0

    for i, name in enumerate(factor_names):
        max_val = FACTOR_MAXES[name]
        if i == len(factor_names) - 1:
            val = total_score - running_sum
        else:
            base = int(max_val * ratio)
            val = max(0, min(max_val, base + random.randint(-2, 2)))
        val = max(0, min(FACTOR_MAXES[name], val))
        factors[name] = val
        running_sum += val

    return factors


def seed():
    random.seed(42)
    with Session(engine) as session:
        # Check if already seeded
        existing = session.execute(
            select(User).where(User.email == "ayushmaan@hivepro.com")
        ).scalar_one_or_none()
        if existing:
            print("Database already seeded. Skipping.")
            return

        # --- Users ---
        hashed = hash_password("password123")
        user_map = {}
        for u in USERS:
            user = User(
                id=uuid.uuid4(),
                email=u["email"],
                hashed_password=hashed,
                full_name=u["full_name"],
                role=u["role"],
            )
            session.add(user)
            user_map[u["email"]] = user
        session.flush()
        print(f"Created {len(USERS)} users")

        # --- Customers ---
        today = date.today()
        now = datetime.now(timezone.utc)
        customer_objects = []
        for c in CUSTOMERS:
            contract_start = today - timedelta(days=random.randint(180, 540))
            renewal_date = today + timedelta(days=random.randint(90, 365))
            owner = user_map[c["cs_owner_email"]]

            customer = Customer(
                id=uuid.uuid4(),
                name=c["name"],
                industry=c["industry"],
                tier=c["tier"],
                contract_start=contract_start,
                renewal_date=renewal_date,
                primary_contact_name=c["primary_contact_name"],
                primary_contact_email=c["primary_contact_email"],
                cs_owner_id=owner.id,
                deployment_mode=c["deployment_mode"],
                product_version=c["product_version"],
                integrations=c["integrations"],
                known_constraints=c["known_constraints"],
            )
            session.add(customer)
            customer_objects.append((customer, c))
        session.flush()
        print(f"Created {len(CUSTOMERS)} customers")

        # --- Health Scores (30 days x 10 customers = 300) ---
        hs_count = 0
        for customer, cdata in customer_objects:
            target = cdata["target_health"]
            for day_offset in range(30):
                calc_time = now - timedelta(days=day_offset, hours=random.randint(0, 8))
                score = max(0, min(100, target + random.randint(-3, 3)))
                risk_level = get_risk_level(score)
                risk_flags = get_risk_flags(score, risk_level)
                factors = generate_factors(score)

                hs = HealthScore(
                    id=uuid.uuid4(),
                    customer_id=customer.id,
                    score=score,
                    factors=factors,
                    risk_flags=risk_flags,
                    risk_level=risk_level,
                    calculated_at=calc_time,
                )
                session.add(hs)
                hs_count += 1
        session.flush()
        print(f"Created {hs_count} health scores")

        # --- Action Items (for at-risk customers, score < 50) ---
        ai_count = 0
        for customer, cdata in customer_objects:
            if cdata["target_health"] >= 50:
                continue
            owner = session.execute(
                select(User).where(User.id == customer.cs_owner_id)
            ).scalar_one()

            num_items = random.randint(2, 3)
            templates = random.sample(ACTION_ITEM_TEMPLATES, k=num_items)
            for title, desc in templates:
                deadline = now + timedelta(days=random.randint(1, 14))
                ai = ActionItem(
                    id=uuid.uuid4(),
                    customer_id=customer.id,
                    source_type="health_check",
                    owner_id=owner.id,
                    title=title,
                    description=desc,
                    deadline=deadline,
                    status="pending",
                )
                session.add(ai)
                ai_count += 1
        session.flush()
        print(f"Created {ai_count} action items")

        # --- Tickets (5 per customer = 50) ---
        ticket_count = 0
        ticket_objects = []
        statuses = ["open", "in_progress", "resolved", "closed"]
        status_weights = [0.3, 0.25, 0.3, 0.15]
        assignees = [user_map["vignesh@hivepro.com"], user_map["chaitanya@hivepro.com"]]

        for customer, cdata in customer_objects:
            integrations = cdata.get("integrations", []) or ["Qualys"]
            for ti in range(5):
                tmpl = random.choice(TICKET_TEMPLATES)
                connector = random.choice(integrations) if integrations else random.choice(CONNECTORS)
                subnet = random.choice(SUBNETS)
                component = random.choice(COMPONENTS)
                days_ago = random.randint(1, 60)
                created = now - timedelta(days=days_ago, hours=random.randint(0, 12))

                summary = tmpl["summary"].format(
                    subnet=subnet, connector=connector, date=(today - timedelta(days=days_ago)).isoformat(),
                    time="03:00 UTC", old_ver="4.1.5", new_ver="4.3.0", component=component,
                    count=random.randint(2, 8),
                )
                description = tmpl["description"].format(
                    subnet=subnet, connector=connector, date=(today - timedelta(days=days_ago)).isoformat(),
                    time="03:00 UTC", old_ver="4.1.5", new_ver="4.3.0", component=component,
                    count=random.randint(2, 8),
                )

                ticket_status = random.choices(statuses, weights=status_weights, k=1)[0]
                resolved_at = None
                if ticket_status in ("resolved", "closed"):
                    resolved_at = created + timedelta(days=random.randint(1, 10))

                # Some tickets have triage results
                triage_result = None
                if random.random() < 0.4:
                    triage_result = {
                        "category": tmpl["type"],
                        "confirmed_severity": tmpl["severity"],
                        "suggested_action": f"Investigate {tmpl['type']} issue and check {connector} integration",
                        "confidence": round(random.uniform(0.7, 0.95), 2),
                    }

                sla_hours = {"P1": 4, "P2": 8, "P3": 24, "P4": 72}
                sla_deadline = created + timedelta(hours=sla_hours.get(tmpl["severity"], 24))

                ticket = Ticket(
                    id=uuid.uuid4(),
                    jira_id=f"CS-{100 + ticket_count}",
                    customer_id=customer.id,
                    summary=summary,
                    description=description,
                    ticket_type=tmpl["type"],
                    severity=tmpl["severity"],
                    status=ticket_status,
                    assigned_to_id=random.choice(assignees).id,
                    triage_result=triage_result,
                    created_at=created,
                    resolved_at=resolved_at,
                    sla_deadline=sla_deadline,
                )
                # Add troubleshoot_result on ~30% of tickets that have triage_result
                troubleshoot_result = None
                if triage_result and random.random() < 0.7:
                    troubleshoot_result = {
                        "root_cause": f"Root cause identified as {tmpl['type']} related issue with {connector}",
                        "confidence": round(random.uniform(0.6, 0.95), 2),
                        "evidence": [
                            f"Similar issue found in {random.randint(2, 5)} past tickets",
                            f"Log analysis shows {tmpl['type']} errors in {component}",
                        ],
                        "resolution_steps": [
                            {"step": 1, "action": f"Verify {connector} connectivity and credentials", "estimated_minutes": 15},
                            {"step": 2, "action": f"Restart {component} service", "estimated_minutes": 10},
                            {"step": 3, "action": "Re-run scan and verify results", "estimated_minutes": 30},
                        ],
                        "estimated_time": f"{random.choice(['30 minutes', '1 hour', '2 hours', '4 hours'])}",
                        "requires_customer_action": random.choice([True, False]),
                        "customer_communication_draft": f"Hi {cdata['primary_contact_name'].split()[0]},\n\nWe've identified the root cause of the {tmpl['type']} issue and have a resolution plan ready. Please allow us to proceed with the fix.\n\nBest regards,\nHivePro Support",
                    }

                ticket = Ticket(
                    id=uuid.uuid4(),
                    jira_id=f"CS-{100 + ticket_count}",
                    customer_id=customer.id,
                    summary=summary,
                    description=description,
                    ticket_type=tmpl["type"],
                    severity=tmpl["severity"],
                    status=ticket_status,
                    assigned_to_id=random.choice(assignees).id,
                    triage_result=triage_result,
                    troubleshoot_result=troubleshoot_result,
                    created_at=created,
                    resolved_at=resolved_at,
                    sla_deadline=sla_deadline,
                )

                session.add(ticket)
                ticket_objects.append((ticket, customer))
                ticket_count += 1
        session.flush()
        print(f"Created {ticket_count} tickets")

        # --- Call Insights (10 per customer = 100) ---
        insight_count = 0
        insight_objects = []
        sentiments = ["positive", "neutral", "negative", "mixed"]
        sentiment_weights = [0.3, 0.35, 0.2, 0.15]

        for customer, cdata in customer_objects:
            integrations = cdata.get("integrations", []) or ["Qualys"]
            for ci_idx in range(10):
                days_ago = random.randint(1, 60)
                call_date = now - timedelta(days=days_ago, hours=random.randint(8, 17))

                tmpl_idx = ci_idx % len(INSIGHT_SUMMARIES)
                connector = random.choice(integrations) if integrations else "Qualys"
                summary = INSIGHT_SUMMARIES[tmpl_idx].format(
                    old_ver="4.1.5", new_ver="4.3.0", quarter=random.randint(1, 4),
                    count=random.randint(2, 10), feature="threat prioritization",
                    connector=connector,
                )

                sentiment = random.choices(sentiments, weights=sentiment_weights, k=1)[0]
                sentiment_map = {"positive": (0.3, 0.9), "neutral": (-0.2, 0.3), "negative": (-0.8, -0.2), "mixed": (-0.3, 0.3)}
                lo, hi = sentiment_map[sentiment]
                sentiment_score = round(random.uniform(lo, hi), 2)

                topics = INSIGHT_TOPICS[tmpl_idx % len(INSIGHT_TOPICS)]
                decisions = INSIGHT_DECISIONS[tmpl_idx % len(INSIGHT_DECISIONS)]
                action_items_data = [
                    {"title": d, "owner": random.choice(["Vignesh", "Chaitanya", cdata["primary_contact_name"]]), "deadline": None}
                    for d in decisions
                ]

                risks = []
                if sentiment in ("negative", "mixed"):
                    risk_options = [
                        "Customer may delay renewal if issues persist",
                        "Engagement declining — risk of shadow IT adoption",
                        "Unresolved P1 eroding confidence in platform",
                        "Competitor evaluation mentioned by customer",
                    ]
                    risks = random.sample(risk_options, k=random.randint(1, 2))

                insight = CallInsight(
                    id=uuid.uuid4(),
                    customer_id=customer.id,
                    fathom_recording_id=f"fathom-{uuid.uuid4().hex[:8]}",
                    call_date=call_date,
                    participants=["Vignesh", cdata["primary_contact_name"]],
                    summary=summary,
                    decisions=decisions,
                    action_items=action_items_data,
                    risks=risks,
                    sentiment=sentiment,
                    sentiment_score=sentiment_score,
                    key_topics=topics,
                    customer_recap_draft=f"Hi {cdata['primary_contact_name'].split()[0]},\n\nThank you for the call today. Here's a summary of what we discussed:\n\n{summary}\n\nBest,\nVignesh",
                )
                session.add(insight)
                insight_objects.append((insight, customer))
                insight_count += 1
        session.flush()
        print(f"Created {insight_count} call insights")

        # --- Agent Logs (200 total) ---
        log_count = 0
        for _ in range(200):
            agent_name = random.choice(AGENT_NAMES)
            customer, cdata = random.choice(customer_objects)
            days_ago = random.randint(0, 30)
            created = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))

            is_success = random.random() < 0.85
            status_val = "completed" if is_success else "failed"
            duration = random.randint(500, 15000)

            event_type = EVENT_TYPES.get(agent_name, "manual_trigger")

            log = AgentLog(
                id=uuid.uuid4(),
                agent_name=agent_name,
                agent_type=AGENT_TYPES.get(agent_name, "control"),
                event_type=event_type,
                trigger_event=random.choice(["cron", "api", "webhook", "manual"]),
                customer_id=customer.id,
                input_summary=f"Processing {event_type} for {cdata['name']}",
                output_summary=f'{{"success": {str(is_success).lower()}, "score": {random.randint(30, 95)}}}' if is_success else f'{{"error": "API timeout after {duration}ms"}}',
                reasoning_summary=f"Analyzed customer data and {'generated result' if is_success else 'encountered error during processing'}",
                status=status_val,
                duration_ms=duration,
                created_at=created,
            )
            session.add(log)
            log_count += 1
        session.flush()
        print(f"Created {log_count} agent logs")

        # --- Events (50 for orchestration flow — covering all event types) ---
        event_count = 0
        event_routing_list = [
            ("jira_ticket_created", "jira_webhook", "ticket_triage"),
            ("jira_ticket_updated", "jira_webhook", "ticket_triage"),
            ("ticket_escalated", "api", "escalation_summary"),
            ("support_bundle_uploaded", "api", "troubleshooter"),
            ("zoom_call_completed", "fathom_sync", "call_intelligence"),
            ("fathom_recording_ready", "fathom_sync", "call_intelligence"),
            ("daily_health_check", "cron", "health_monitor"),
            ("manual_health_check", "manual", "health_monitor"),
            ("renewal_approaching", "cron", "qbr_value"),
            ("new_enterprise_customer", "api", "sow_prerequisite"),
            ("deployment_started", "api", "deployment_intelligence"),
        ]

        for i in range(50):
            customer, cdata = random.choice(customer_objects)
            evt_type, evt_source, evt_agent = event_routing_list[i % len(event_routing_list)]
            days_ago = random.randint(0, 30)
            created = now - timedelta(days=days_ago, hours=random.randint(0, 12))

            payload = {"customer_name": cdata["name"], "source": "seed"}
            if evt_type in ("jira_ticket_created", "jira_ticket_updated"):
                payload["jira_id"] = f"CS-{100 + random.randint(0, 49)}"
                payload["summary"] = random.choice(TICKET_TEMPLATES)["summary"].format(
                    subnet=random.choice(SUBNETS), connector=random.choice(CONNECTORS),
                    date=today.isoformat(), time="03:00 UTC", old_ver="4.1.5",
                    new_ver="4.3.0", component=random.choice(COMPONENTS), count=3,
                )
            elif evt_type == "deployment_started":
                payload["deployment_mode"] = cdata.get("deployment_mode", "Cloud")
                payload["target_version"] = cdata.get("product_version", "4.3.0")
            elif evt_type == "renewal_approaching":
                payload["renewal_date"] = (today + timedelta(days=random.randint(30, 90))).isoformat()
                payload["tier"] = cdata.get("tier", "enterprise")

            evt = Event(
                id=uuid.uuid4(),
                event_type=evt_type,
                source=evt_source,
                payload=payload,
                status=random.choice(["completed", "completed", "completed", "failed"]),
                routed_to=evt_agent,
                customer_id=customer.id,
                created_at=created,
                processed_at=created + timedelta(seconds=random.randint(1, 30)),
            )
            session.add(evt)
            event_count += 1
        session.flush()
        print(f"Created {event_count} events")

        # --- Alerts (15 across at-risk customers) ---
        alert_count = 0
        at_risk_customers = [(c, d) for c, d in customer_objects if d["target_health"] < 60]
        alert_statuses = ["open", "acknowledged", "resolved"]
        alert_status_weights = [0.4, 0.3, 0.3]

        for i in range(15):
            customer, cdata = at_risk_customers[i % len(at_risk_customers)]
            tmpl = ALERT_TEMPLATES[i % len(ALERT_TEMPLATES)]
            days_ago = random.randint(0, 14)
            created = now - timedelta(days=days_ago)

            title = tmpl["title"].format(
                customer=cdata["name"], threshold=50, old_score=55, new_score=cdata["target_health"],
                ticket_id=f"CS-{100 + i}", hours=random.randint(5, 24),
                scores=f"{random.uniform(-0.5, -0.1):.1f}, {random.uniform(-0.6, -0.2):.1f}, {random.uniform(-0.7, -0.3):.1f}",
                topic="deployment issues", days=random.randint(14, 30),
            )
            description = tmpl["description"].format(
                customer=cdata["name"], threshold=50, old_score=55, new_score=cdata["target_health"],
                ticket_id=f"CS-{100 + i}", hours=random.randint(5, 24),
                scores=f"{random.uniform(-0.5, -0.1):.1f}, {random.uniform(-0.6, -0.2):.1f}, {random.uniform(-0.7, -0.3):.1f}",
                topic="deployment issues", days=random.randint(14, 30),
            )

            alert_status = random.choices(alert_statuses, weights=alert_status_weights, k=1)[0]
            resolved_at = created + timedelta(days=random.randint(1, 5)) if alert_status == "resolved" else None

            alert = Alert(
                id=uuid.uuid4(),
                customer_id=customer.id,
                alert_type=tmpl["type"],
                severity=tmpl["severity"],
                title=title,
                description=description,
                suggested_action=tmpl["action"],
                assigned_to_id=customer.cs_owner_id,
                status=alert_status,
                created_at=created,
                resolved_at=resolved_at,
            )
            session.add(alert)
            alert_count += 1
        session.flush()
        print(f"Created {alert_count} alerts")

        # --- Reports (8 total: 3 weekly_digest, 3 monthly_report, 2 qbr) ---
        report_count = 0
        report_customers = random.sample(customer_objects, min(6, len(customer_objects)))

        # 3 Weekly Digests
        for i in range(3):
            customer, cdata = report_customers[i % len(report_customers)]
            period_end = today - timedelta(days=i * 7)
            period_start = period_end - timedelta(days=7)
            report = Report(
                id=uuid.uuid4(),
                report_type="weekly_digest",
                customer_id=customer.id,
                title=f"Weekly Digest — {period_start.strftime('%b %d')} to {period_end.strftime('%b %d, %Y')}",
                content={
                    "summary": f"Weekly summary for {cdata['name']}: {random.randint(2, 8)} tickets processed, health score {'stable' if cdata['target_health'] > 60 else 'declining'}.",
                    "tickets_opened": random.randint(1, 5),
                    "tickets_resolved": random.randint(0, 4),
                    "avg_resolution_hours": round(random.uniform(4, 48), 1),
                    "health_score_change": random.randint(-5, 5),
                    "calls_completed": random.randint(1, 4),
                    "key_highlights": [
                        f"Resolved P1 ticket on {random.choice(CONNECTORS)} integration",
                        f"Customer sentiment {'improved' if random.random() > 0.5 else 'steady'} this week",
                    ],
                    "action_items_pending": random.randint(1, 5),
                },
                period_start=period_start,
                period_end=period_end,
                generated_at=now - timedelta(days=i * 7),
            )
            session.add(report)
            report_count += 1

        # 3 Monthly Reports
        for i in range(3):
            customer, cdata = report_customers[(i + 2) % len(report_customers)]
            period_end = today - timedelta(days=i * 30)
            period_start = period_end - timedelta(days=30)
            report = Report(
                id=uuid.uuid4(),
                report_type="monthly_report",
                customer_id=customer.id,
                title=f"Monthly Report — {period_start.strftime('%B %Y')}",
                content={
                    "executive_summary": f"Monthly performance review for {cdata['name']}. Overall health {'above' if cdata['target_health'] > 60 else 'below'} target threshold.",
                    "tickets": {
                        "total": random.randint(8, 20),
                        "resolved": random.randint(5, 15),
                        "p1_count": random.randint(0, 3),
                        "avg_resolution_days": round(random.uniform(1, 7), 1),
                    },
                    "health_trend": [
                        {"week": f"W{w}", "score": max(20, min(100, cdata["target_health"] + random.randint(-8, 8)))}
                        for w in range(1, 5)
                    ],
                    "engagement": {
                        "calls": random.randint(4, 12),
                        "avg_sentiment": round(random.uniform(-0.3, 0.8), 2),
                        "nps_score": random.choice([7, 8, 9, 6, 8]),
                    },
                    "recommendations": [
                        "Schedule proactive health review",
                        f"Optimize {random.choice(CONNECTORS)} scan windows for better performance",
                    ],
                },
                period_start=period_start,
                period_end=period_end,
                generated_at=now - timedelta(days=i * 30 + 1),
            )
            session.add(report)
            report_count += 1

        # 2 QBR Reports
        for i in range(2):
            customer, cdata = report_customers[(i + 4) % len(report_customers)]
            period_end = today - timedelta(days=i * 90)
            period_start = period_end - timedelta(days=90)
            report = Report(
                id=uuid.uuid4(),
                report_type="qbr",
                customer_id=customer.id,
                title=f"Quarterly Business Review — {period_end.strftime('%B %Y')}",
                content={
                    "executive_summary": f"Q{((period_end.month - 1) // 3) + 1} review for {cdata['name']}. Partnership continues to deliver value with {random.randint(60, 95)}% vulnerability coverage.",
                    "health_trend_narrative": f"Health score has {'remained stable' if cdata['target_health'] > 60 else 'shown improvement needs'} over the quarter, averaging {cdata['target_health']}.",
                    "ticket_analysis": {
                        "summary": f"{random.randint(15, 40)} tickets handled this quarter",
                        "total_tickets": random.randint(15, 40),
                        "resolved_tickets": random.randint(10, 35),
                        "avg_resolution_days": round(random.uniform(1.5, 5.0), 1),
                        "top_categories": random.sample(["scan_failure", "connector_issue", "deployment", "performance", "configuration"], 3),
                    },
                    "call_sentiment_analysis": {
                        "summary": f"Overall sentiment {'positive' if cdata['target_health'] > 60 else 'mixed'} across {random.randint(8, 20)} calls",
                        "avg_sentiment_score": round(random.uniform(-0.2, 0.7), 2),
                        "trend": random.choice(["improving", "stable", "declining"]),
                        "key_concerns": ["Scan performance during peak hours", "Integration reliability"],
                    },
                    "achievements": [
                        f"Reduced mean time to resolution by {random.randint(10, 30)}%",
                        f"Onboarded {random.randint(1, 3)} new integrations",
                        "Zero P1 SLA breaches this quarter",
                    ],
                    "risks_and_concerns": [
                        "Upcoming renewal requires executive engagement",
                        f"Legacy {cdata.get('deployment_mode', 'OVA')} deployment may need upgrade path",
                    ],
                    "recommendations": [
                        "Upgrade to latest product version for performance improvements",
                        "Expand scanning coverage to include cloud assets",
                        "Schedule executive business review before renewal",
                    ],
                    "next_quarter_goals": [
                        "Achieve 95% vulnerability scan coverage",
                        "Reduce average ticket resolution time to under 48 hours",
                        "Complete migration to latest platform version",
                    ],
                    "reasoning": "QBR generated from 90-day customer data aggregation.",
                },
                period_start=period_start,
                period_end=period_end,
                generated_at=now - timedelta(days=i * 90 + 2),
            )
            session.add(report)
            report_count += 1
        session.flush()
        print(f"Created {report_count} reports")

        session.commit()
        print("Database seed complete!")

    # --- ChromaDB Embeddings ---
    print("\nEmbedding data into ChromaDB...")
    try:
        from app.services import rag_service

        # Embed tickets
        embedded_tickets = 0
        with Session(engine) as session:
            tickets = session.execute(select(Ticket).limit(50)).scalars().all()
            for t in tickets:
                customer = session.execute(
                    select(Customer.name).where(Customer.id == t.customer_id)
                ).scalar_one_or_none()
                text = f"{t.summary} {t.description or ''}"
                metadata = {
                    "jira_id": t.jira_id or "",
                    "customer_name": customer or "",
                    "severity": t.severity or "",
                    "status": t.status or "",
                    "ticket_type": t.ticket_type or "",
                }
                rag_service.embed_ticket(str(t.id), text, metadata)
                embedded_tickets += 1
        print(f"Embedded {embedded_tickets} tickets into ChromaDB")

        # Embed insights
        embedded_insights = 0
        with Session(engine) as session:
            insights = session.execute(select(CallInsight).limit(100)).scalars().all()
            for ci in insights:
                customer = session.execute(
                    select(Customer.name).where(Customer.id == ci.customer_id)
                ).scalar_one_or_none()
                topics = ", ".join(ci.key_topics) if ci.key_topics else ""
                text = f"{ci.summary or ''} Topics: {topics}"
                metadata = {
                    "customer_name": customer or "",
                    "sentiment": ci.sentiment or "",
                    "sentiment_score": str(ci.sentiment_score or 0),
                }
                rag_service.embed_insight(str(ci.id), text, metadata)
                embedded_insights += 1
        print(f"Embedded {embedded_insights} insights into ChromaDB")

    except Exception as e:
        print(f"ChromaDB embedding failed (non-fatal): {e}")

    print("\nSeed complete!")


if __name__ == "__main__":
    seed()
