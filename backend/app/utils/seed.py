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
- 200 agent logs (all 13 agents)
- 50 events (all 11 event types)
- 15 alerts
- 8 reports (3 weekly_digest, 3 monthly_report, 2 qbr)
- ChromaDB embeddings for tickets and insights
- 50 agent execution rounds (5 pipeline runs × ~10 stages)
- 40 agent messages (5 delegation threads)
- 30 episodic memories (ChromaDB)
- 15 shared knowledge entries (ChromaDB)
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
from app.models.agent_execution_round import AgentExecutionRound
from app.models.agent_message import AgentMessage
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
        "jira_project_key": "ACME",
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
        "jira_project_key": "BETA",
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
        "jira_project_key": "GAMMA",
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
        "jira_project_key": "DELTA",
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
        "jira_project_key": "EPSI",
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
        "jira_project_key": "ZETA",
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
        "jira_project_key": "ETA",
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
        "jira_project_key": "THETA",
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
        "jira_project_key": "IOTA",
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
        "jira_project_key": "KAPPA",
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
    "health_monitor", "fathom_agent", "ticket_triage", "customer_memory",
    "troubleshooter", "escalation_summary", "qbr_value", "sow_prerequisite", "deployment_intelligence",
]
AGENT_TYPES = {
    "health_monitor": "value", "fathom_agent": "value", "ticket_triage": "support",
    "customer_memory": "control", "troubleshooter": "support", "escalation_summary": "support",
    "qbr_value": "value", "sow_prerequisite": "delivery", "deployment_intelligence": "delivery",
}
EVENT_TYPES = {
    "health_monitor": "daily_health_check",
    "fathom_agent": "fathom_recording_ready",
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


def is_seeded() -> bool:
    """Check if the database already has seed data."""
    with Session(engine) as session:
        existing = session.execute(
            select(User).where(User.email == "ayushmaan@hivepro.com")
        ).scalar_one_or_none()
        return existing is not None


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
                jira_project_key=c.get("jira_project_key"),
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
            ("zoom_call_completed", "fathom_sync", "fathom_agent"),
            ("fathom_recording_ready", "fathom_sync", "fathom_agent"),
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

    # --- V2: Agent Execution Rounds + Messages ---
    _seed_execution_rounds(engine)
    _seed_agent_messages(engine)
    _seed_episodic_memories()
    _seed_shared_knowledge()
    _seed_meeting_knowledge()

    print("\nSeed complete!")


# ═══════════════════════════════════════════════════════════════════
# V2 Seed Data: Agentic Architecture
# ═══════════════════════════════════════════════════════════════════

# Agent identity lookup
AGENT_NAMES_V2 = {
    "cso_orchestrator": "Naveen Kapoor",
    "support_lead": "Rachel Torres",
    "value_lead": "Damon Reeves",
    "delivery_lead": "Priya Mehta",
    "triage_agent": "Kai Nakamura",
    "troubleshooter_agent": "Leo Petrov",
    "escalation_agent": "Maya Santiago",
    "health_monitor_agent": "Dr. Aisha Okafor",
    "fathom_agent": "Jordan Ellis",
    "qbr_agent": "Sofia Marquez",
    "sow_agent": "Ethan Brooks",
    "deployment_intel_agent": "Zara Kim",
    "customer_memory": "Atlas",
}

AGENT_TIERS = {
    "cso_orchestrator": 1,
    "support_lead": 2, "value_lead": 2, "delivery_lead": 2,
    "triage_agent": 3, "troubleshooter_agent": 3, "escalation_agent": 3,
    "health_monitor_agent": 3, "fathom_agent": 3, "qbr_agent": 3,
    "sow_agent": 3, "deployment_intel_agent": 3,
    "customer_memory": 4,
}

AGENT_LANES = {
    "cso_orchestrator": None,
    "support_lead": "support", "value_lead": "value", "delivery_lead": "delivery",
    "triage_agent": "support", "troubleshooter_agent": "support", "escalation_agent": "support",
    "health_monitor_agent": "value", "fathom_agent": "value", "qbr_agent": "value",
    "sow_agent": "delivery", "deployment_intel_agent": "delivery",
    "customer_memory": None,
}

# Pipeline stage definitions per tier
TIER_STAGES = {
    1: [
        ("Event Analysis", "perceive"),
        ("Context Gathering", "retrieve"),
        ("Strategic Decomposition", "think"),
        ("Delegation", "act"),
        ("Quality Evaluation", "quality_gate"),
        ("Synthesis", "finalize"),
    ],
    2: [
        ("Task Reception", "perceive"),
        ("Context Retrieval", "retrieve"),
        ("Task Planning", "think"),
        ("Specialist Coordination", "act"),
        ("Lane Synthesis", "finalize"),
    ],
    3: [
        ("Task Perception", "perceive"),
        ("Memory Retrieval", "retrieve"),
        ("Analysis", "think"),
        ("Execution", "act"),
        ("Self-Reflection", "reflect"),
    ],
    4: [
        ("Request Parsing", "perceive"),
        ("Data Retrieval", "act"),
    ],
}


def _seed_execution_rounds(engine):
    """Create 5 sample pipeline runs (~50 total rounds)."""
    print("\nSeeding agent execution rounds...")

    # 5 pipeline runs across different tiers/agents
    pipeline_runs = [
        {
            "agent_id": "cso_orchestrator",
            "event_type": "jira_ticket_created",
            "customer": "Acme Corp",
        },
        {
            "agent_id": "support_lead",
            "event_type": "jira_ticket_created",
            "customer": "Acme Corp",
        },
        {
            "agent_id": "triage_agent",
            "event_type": "jira_ticket_created",
            "customer": "Acme Corp",
        },
        {
            "agent_id": "fathom_agent",
            "event_type": "fathom_call_recorded",
            "customer": "TechVault",
        },
        {
            "agent_id": "health_monitor_agent",
            "event_type": "cron_health_check",
            "customer": "CyberNova",
        },
    ]

    with Session(engine) as session:
        # Get some event IDs and customer IDs to reference
        events = session.execute(select(Event.id).limit(5)).scalars().all()
        customers = session.execute(
            select(Customer.id, Customer.name)
        ).all()
        customer_map = {c.name: c.id for c in customers}

        round_count = 0
        for i, run in enumerate(pipeline_runs):
            execution_id = uuid.uuid4()
            agent_id = run["agent_id"]
            tier = AGENT_TIERS[agent_id]
            stages = TIER_STAGES[tier]
            event_id = events[i] if i < len(events) else None
            customer_id = customer_map.get(run["customer"])
            base_time = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))

            for stage_num, (stage_name, stage_type) in enumerate(stages, 1):
                duration = random.randint(200, 3000)
                tokens = random.randint(500, 4000)

                # Build realistic tools_called for act stages
                tools_called = []
                if stage_type == "act":
                    tools_called = [
                        {
                            "tool_name": "query_customer_db",
                            "arguments": {"customer_id": str(customer_id) if customer_id else "cust-001"},
                            "result_preview": f"{run['customer']}, Enterprise tier",
                            "duration_ms": random.randint(50, 200),
                        }
                    ]
                elif stage_type == "retrieve":
                    tools_called = [
                        {
                            "tool_name": "search_knowledge_base",
                            "arguments": {"query": f"recent issues {run['customer']}"},
                            "result_preview": "3 relevant entries found",
                            "duration_ms": random.randint(100, 400),
                        }
                    ]

                # Metadata varies by stage type
                metadata = {}
                if stage_type == "retrieve":
                    metadata = {"memory_retrieved": random.randint(1, 5)}
                elif stage_type == "act" and tier <= 2:
                    metadata = {"delegated_to": ["triage_agent", "troubleshooter_agent"]}
                elif stage_type == "quality_gate":
                    metadata = {"quality_gate_passed": True, "retry_count": 0}

                status = "completed"
                if i == 0 and stage_num == len(stages):
                    status = "running"  # Last run still in progress

                confidence = None
                if stage_type == "reflect":
                    confidence = round(random.uniform(0.7, 0.95), 2)

                session.add(AgentExecutionRound(
                    execution_id=execution_id,
                    event_id=event_id,
                    agent_id=agent_id,
                    agent_name=AGENT_NAMES_V2[agent_id],
                    tier=tier,
                    stage_number=stage_num,
                    stage_name=stage_name,
                    lane=AGENT_LANES[agent_id],
                    stage_type=stage_type,
                    input_summary=f"Processing {run['event_type']} for {run['customer']}",
                    output_summary=f"Stage {stage_name} completed — {stage_type} output generated",
                    tools_called=tools_called,
                    tokens_used=tokens,
                    duration_ms=duration,
                    confidence=confidence,
                    status=status,
                    metadata_=metadata,
                    created_at=base_time + timedelta(seconds=stage_num * 5),
                ))
                round_count += 1

        session.commit()
        print(f"Created {round_count} execution rounds across {len(pipeline_runs)} pipeline runs")


def _seed_agent_messages(engine):
    """Create 5 delegation threads (~40 messages total)."""
    print("Seeding agent messages...")

    with Session(engine) as session:
        events = session.execute(select(Event.id).limit(5)).scalars().all()
        customers = session.execute(
            select(Customer.id, Customer.name)
        ).all()

        msg_count = 0
        threads = [
            # Thread 1: Ticket triage flow (8 messages)
            {
                "event_idx": 0,
                "customer": "Acme Corp",
                "messages": [
                    ("cso_orchestrator", "support_lead", "task_assignment", "down", 7,
                     "New P1 ticket from Acme Corp — scan failure on subnet 10.0.1.x. Please coordinate triage and troubleshooting. SLA: 4 hours."),
                    ("support_lead", "triage_agent", "task_assignment", "down", 7,
                     "Incoming P1 from Acme Corp. Classify this ticket, check for similar past issues, and provide severity assessment."),
                    ("triage_agent", "support_lead", "deliverable", "up", 5,
                     "Classification complete. Type: scan_failure, Severity: P1-Critical. Found 3 similar tickets — all resolved by restarting scan engine. Recommend immediate troubleshooting."),
                    ("support_lead", "troubleshooter_agent", "task_assignment", "down", 7,
                     "P1 scan failure for Acme Corp. Triage suggests scan engine restart. Investigate root cause and provide resolution steps."),
                    ("troubleshooter_agent", "support_lead", "deliverable", "up", 5,
                     "Root cause identified: scan engine memory leak after v4.2.1 patch. Resolution: restart scan engine, apply hotfix KB-2024-0312. ETA: 30 minutes."),
                    ("support_lead", "cso_orchestrator", "deliverable", "up", 5,
                     "Ticket triaged and diagnosed. Root cause: scan engine memory leak (v4.2.1). Resolution in progress — hotfix being applied. ETA: 30 min."),
                    ("cso_orchestrator", "support_lead", "feedback", "down", 5,
                     "Good work. Fast turnaround on the P1. Make sure the hotfix application is tracked and customer is notified of resolution."),
                    ("support_lead", "escalation_agent", "request", "down", 4,
                     "Monitor Acme Corp ticket HIVE-4521 for SLA compliance. Alert me if resolution exceeds 4-hour window."),
                ],
            },
            # Thread 2: Call intelligence flow (7 messages)
            {
                "event_idx": 1,
                "customer": "TechVault",
                "messages": [
                    ("cso_orchestrator", "value_lead", "task_assignment", "down", 6,
                     "New call recording from TechVault QBR prep meeting. Extract intelligence and flag any risks."),
                    ("value_lead", "fathom_agent", "task_assignment", "down", 6,
                     "Analyze TechVault QBR prep call. Extract: sentiment, action items, risk signals, competitor mentions."),
                    ("fathom_agent", "value_lead", "deliverable", "up", 5,
                     "Call analysis complete. Sentiment: mixed (0.45). Key risk: customer mentioned evaluating CrowdStrike for endpoint. Action items: 3 follow-ups needed. Decision: delay renewal discussion until product roadmap shared."),
                    ("value_lead", "health_monitor_agent", "request", "sideways", 6,
                     "TechVault showing competitor evaluation signals. Please check latest health score and flag if trending down."),
                    ("health_monitor_agent", "value_lead", "deliverable", "sideways", 6,
                     "TechVault health: 58 (watch zone). Down 12 points in 14 days. Factors: engagement declining, sentiment dropping. Recommend immediate attention."),
                    ("value_lead", "cso_orchestrator", "deliverable", "up", 7,
                     "TechVault intelligence: Mixed sentiment call, competitor evaluation (CrowdStrike), health score 58 and declining. This customer needs proactive engagement — recommend executive outreach."),
                    ("cso_orchestrator", "value_lead", "feedback", "down", 5,
                     "Critical finding. I'll flag this for the CS team. Please have Sofia start a QBR prep focused on competitive positioning."),
                ],
            },
            # Thread 3: Health alert escalation (8 messages)
            {
                "event_idx": 2,
                "customer": "CyberNova",
                "messages": [
                    ("cso_orchestrator", "value_lead", "task_assignment", "down", 8,
                     "URGENT: CyberNova health score dropped to 35. Renewal in 60 days. Full health analysis and escalation assessment needed."),
                    ("value_lead", "health_monitor_agent", "task_assignment", "down", 8,
                     "CyberNova critical health alert. Run full analysis — what's driving the decline? Provide 30-day trend breakdown."),
                    ("health_monitor_agent", "value_lead", "deliverable", "up", 7,
                     "CyberNova 30-day analysis: Score dropped from 72 to 35. Primary drivers: 4 unresolved P1 tickets (resolution_rate tanked), 2 missed SLAs, engagement score zero (no calls in 3 weeks). This is a churn risk."),
                    ("value_lead", "cso_orchestrator", "escalation", "up", 9,
                     "ESCALATION: CyberNova is a churn risk. Health 35, down from 72. 4 unresolved P1s, 2 SLA breaches, zero engagement in 3 weeks. Renewal in 60 days. Recommend immediate executive intervention."),
                    ("cso_orchestrator", "support_lead", "task_assignment", "down", 9,
                     "CyberNova emergency: 4 unresolved P1 tickets need immediate attention. Get status on all 4 and create resolution plan. This is churn-critical."),
                    ("support_lead", "troubleshooter_agent", "task_assignment", "down", 9,
                     "CyberNova — investigate all 4 open P1 tickets. I need root cause for each and estimated resolution timeline. Priority override: drop everything else."),
                    ("troubleshooter_agent", "support_lead", "deliverable", "up", 7,
                     "CyberNova P1 investigation complete. 2 tickets are blocked on customer infra access (need VPN credentials). 1 is a known product bug (fix in v4.3). 1 can be resolved today with config change. Recommended: emergency call with customer IT."),
                    ("support_lead", "cso_orchestrator", "deliverable", "up", 8,
                     "CyberNova P1 status: 1 resolvable today, 1 awaiting product fix (v4.3), 2 blocked on customer access. Recommend emergency call to unblock VPN access and demonstrate commitment."),
                ],
            },
            # Thread 4: QBR generation (9 messages)
            {
                "event_idx": 3,
                "customer": "DataShield",
                "messages": [
                    ("cso_orchestrator", "value_lead", "task_assignment", "down", 5,
                     "Quarterly review due for DataShield. Coordinate QBR report generation."),
                    ("cso_orchestrator", "delivery_lead", "task_assignment", "down", 5,
                     "DataShield QBR — need deployment status and SOW compliance for the report."),
                    ("value_lead", "qbr_agent", "task_assignment", "down", 5,
                     "Generate QBR report for DataShield. Include health trends, ticket summary, call insights, and recommendations."),
                    ("value_lead", "fathom_agent", "request", "down", 4,
                     "Pull last 3 months of call summaries for DataShield QBR."),
                    ("delivery_lead", "deployment_intel_agent", "task_assignment", "down", 5,
                     "DataShield QBR — provide deployment health summary and any SOW milestone updates."),
                    ("fathom_agent", "value_lead", "deliverable", "up", 4,
                     "DataShield call summary (Q4): 8 calls, avg sentiment 0.72, key themes: product adoption, feature requests for API integration. No competitor mentions."),
                    ("deployment_intel_agent", "delivery_lead", "deliverable", "up", 4,
                     "DataShield deployment: Healthy. All 3 SOW milestones on track. v4.2 deployed last month, no rollback issues. Risk: low."),
                    ("qbr_agent", "value_lead", "deliverable", "up", 5,
                     "QBR report generated for DataShield. Health: 78 (stable). 12 tickets (all resolved). Positive engagement trend. Recommendation: upsell API integration module."),
                    ("value_lead", "cso_orchestrator", "deliverable", "up", 5,
                     "DataShield QBR complete. Health stable at 78, all tickets resolved, positive engagement. Delivery on track. Upsell opportunity: API integration."),
                ],
            },
            # Thread 5: Deployment risk (8 messages)
            {
                "event_idx": 4,
                "customer": "SecureNet",
                "messages": [
                    ("cso_orchestrator", "delivery_lead", "task_assignment", "down", 7,
                     "SecureNet just deployed v4.3 hotfix. Monitor for any issues — last deployment caused scan failures."),
                    ("delivery_lead", "deployment_intel_agent", "task_assignment", "down", 7,
                     "SecureNet v4.3 deployment. Run post-deployment health check and correlate with any new tickets in the last 24 hours."),
                    ("deployment_intel_agent", "delivery_lead", "deliverable", "up", 6,
                     "SecureNet post-deployment check: 1 new ticket (scan timeout on large subnets). Similar to pre-hotfix issue pattern. Deployment health: degraded. Recommend rollback assessment."),
                    ("delivery_lead", "cso_orchestrator", "escalation", "up", 8,
                     "SecureNet deployment concern: v4.3 hotfix may not have resolved the scan timeout issue. New ticket matching old pattern. Recommending support lane involvement."),
                    ("cso_orchestrator", "support_lead", "task_assignment", "down", 8,
                     "SecureNet: deployment team flagged recurring scan timeout after v4.3. Check the new ticket and compare to pre-hotfix tickets."),
                    ("support_lead", "troubleshooter_agent", "task_assignment", "down", 8,
                     "SecureNet scan timeout recurring post v4.3. Compare new ticket to HIVE-3891 and HIVE-3920. Is this the same root cause?"),
                    ("troubleshooter_agent", "support_lead", "deliverable", "up", 6,
                     "Compared tickets: same subnet range, same timeout threshold. Root cause is different — v4.3 fixed the memory leak but introduced a new timeout on subnets >500 hosts. Engineering ticket needed."),
                    ("support_lead", "cso_orchestrator", "deliverable", "up", 7,
                     "SecureNet analysis: v4.3 fixed original issue but introduced new timeout bug for large subnets. Engineering ticket required. Customer impact: moderate (2 of 12 subnets affected)."),
                ],
            },
        ]

        for thread_data in threads:
            thread_id = uuid.uuid4()
            execution_id = uuid.uuid4()
            event_id = events[thread_data["event_idx"]] if thread_data["event_idx"] < len(events) else None

            # Find customer_id
            customer_name = thread_data["customer"]
            customer_row = next((c for c in customers if c.name == customer_name), None)
            customer_id = customer_row.id if customer_row else None

            parent_id = None
            for j, (from_a, to_a, msg_type, direction, priority, content) in enumerate(thread_data["messages"]):
                msg_id = uuid.uuid4()
                if j == 0:
                    parent_id = None  # Thread starter has no parent

                lane = AGENT_LANES.get(from_a)
                msg = AgentMessage(
                    id=msg_id,
                    thread_id=thread_id,
                    parent_id=parent_id,
                    from_agent=from_a,
                    from_name=AGENT_NAMES_V2[from_a],
                    to_agent=to_a,
                    to_name=AGENT_NAMES_V2[to_a],
                    message_type=msg_type,
                    direction=direction,
                    content=content,
                    priority=priority,
                    event_id=event_id,
                    execution_id=execution_id,
                    customer_id=customer_id,
                    status="completed" if j < len(thread_data["messages"]) - 1 else "pending",
                    metadata_={"lane": lane, "tags": [customer_name.lower().replace(" ", "-")]},
                )
                session.add(msg)
                parent_id = msg_id  # Next message references this one
                msg_count += 1

        session.commit()
        print(f"Created {msg_count} agent messages across {len(threads)} threads")


def _seed_episodic_memories():
    """Seed 30 episodic memory entries in ChromaDB (~3 per agent)."""
    print("Seeding episodic memories into ChromaDB...")

    try:
        from app.chromadb_client import episodic_memory

        if episodic_memory is None:
            print("  Skipped — episodic_memory collection not available")
            return

        memories = [
            # Triage Agent (Kai)
            ("triage_agent", "Kai Nakamura", "Acme Corp", "jira_ticket_created", 7,
             "Triaged P1 scan failure for Acme Corp. Found 3 similar past tickets — all resolved by restarting scan engine. Classification confidence: 0.92. Pattern: scan engine memory leak after v4.2.1 patch."),
            ("triage_agent", "Kai Nakamura", "TechVault", "jira_ticket_created", 5,
             "Triaged P3 dashboard loading issue for TechVault. Low severity, likely browser cache. No similar past tickets found. Recommended basic troubleshooting steps."),
            ("triage_agent", "Kai Nakamura", "CyberNova", "jira_ticket_created", 8,
             "Triaged P1 authentication failure for CyberNova. Critical — blocking all scans. Similar to HIVE-2891 from 3 months ago. Escalated immediately to troubleshooting."),
            # Troubleshooter Agent (Leo)
            ("troubleshooter_agent", "Leo Petrov", "Acme Corp", "jira_ticket_created", 8,
             "Root cause analysis for Acme Corp scan failure. Memory leak in scan engine v4.2.1. Resolution: restart + hotfix KB-2024-0312. Total investigation time: 15 min. Confidence: 0.94."),
            ("troubleshooter_agent", "Leo Petrov", "SecureNet", "jira_ticket_created", 9,
             "Complex troubleshooting for SecureNet. v4.3 hotfix introduced new timeout on subnets >500 hosts. Different root cause than original issue. Engineering ticket required. Lesson: always test with large subnet configs."),
            ("troubleshooter_agent", "Leo Petrov", "DataShield", "jira_ticket_created", 4,
             "Investigated DataShield report generation timeout. Simple fix — increased DB query timeout from 30s to 60s. Low complexity issue."),
            # Health Monitor (Dr. Aisha)
            ("health_monitor_agent", "Dr. Aisha Okafor", "CyberNova", "cron_health_check", 9,
             "Critical health decline detected for CyberNova: 72 → 35 in 30 days. Primary drivers: 4 unresolved P1 tickets, 2 SLA breaches, zero engagement in 3 weeks. Flagged as churn risk with renewal in 60 days."),
            ("health_monitor_agent", "Dr. Aisha Okafor", "TechVault", "cron_health_check", 7,
             "TechVault health declining: 70 → 58 in 14 days. Engagement dropping, sentiment negative in recent call. Competitor evaluation signals detected. Recommend proactive outreach."),
            ("health_monitor_agent", "Dr. Aisha Okafor", "DataShield", "cron_health_check", 3,
             "DataShield routine health check. Score stable at 78. All metrics within normal ranges. No action needed."),
            # Call Intel (Jordan)
            ("fathom_agent", "Jordan Ellis", "TechVault", "fathom_call_recorded", 8,
             "Analyzed TechVault QBR prep call. Mixed sentiment (0.45). Critical finding: customer evaluating CrowdStrike for endpoint. 3 action items extracted. Recommendation: share product roadmap to counter competitive threat."),
            ("fathom_agent", "Jordan Ellis", "Acme Corp", "fathom_call_recorded", 5,
             "Analyzed Acme Corp weekly sync. Positive sentiment (0.78). Customer satisfied with recent P1 resolution. Minor feature request for automated scan scheduling."),
            ("fathom_agent", "Jordan Ellis", "DataShield", "fathom_call_recorded", 4,
             "DataShield quarterly check-in. Sentiment positive (0.82). Strong product adoption. Key topic: API integration interest. Upsell opportunity flagged."),
            # Escalation Agent (Maya)
            ("escalation_agent", "Maya Santiago", "CyberNova", "jira_ticket_created", 9,
             "Escalated CyberNova to executive level. 4 P1 tickets unresolved, 2 SLA breaches, renewal in 60 days. Severity: critical. Stakeholders notified. Emergency call scheduled."),
            ("escalation_agent", "Maya Santiago", "SecureNet", "jira_ticket_created", 7,
             "Near-escalation for SecureNet deployment issue. Held off pending troubleshooting result. Deployment risk flagged but customer impact moderate (2/12 subnets). Monitoring SLA."),
            ("escalation_agent", "Maya Santiago", "Acme Corp", "jira_ticket_created", 5,
             "SLA monitoring for Acme Corp P1 ticket HIVE-4521. Resolution completed within 2-hour window. No escalation needed. SLA compliance: met."),
            # QBR Agent (Sofia)
            ("qbr_agent", "Sofia Marquez", "DataShield", "cron_qbr_schedule", 6,
             "Generated Q4 QBR for DataShield. Health stable at 78, 12 tickets all resolved, positive call sentiment (0.82 avg). Upsell recommendation: API integration module. Report length: 2,400 words."),
            ("qbr_agent", "Sofia Marquez", "Acme Corp", "cron_qbr_schedule", 7,
             "Generated Q4 QBR for Acme Corp. Health recovered to 68 after P1 resolution. Key narrative: responsive support during crisis built trust. Recommendation: proactive scan engine monitoring."),
            ("qbr_agent", "Sofia Marquez", "TechVault", "cron_qbr_schedule", 8,
             "Generated Q4 QBR for TechVault. Health declining — 58 and trending down. Key concern: competitive evaluation. QBR strategy: lead with product roadmap, address feature gaps."),
            # SOW Agent (Ethan)
            ("sow_agent", "Ethan Brooks", "DataShield", "manual_sow_request", 5,
             "SOW review for DataShield: All 3 milestones on track. Deliverable 1 completed ahead of schedule. No scope creep detected. Next milestone due in 3 weeks."),
            ("sow_agent", "Ethan Brooks", "SecureNet", "manual_sow_request", 7,
             "SOW review for SecureNet: 1 of 4 milestones delayed due to deployment issues. Scope creep detected — customer requesting additional subnet coverage not in original SOW. Recommend change order."),
            ("sow_agent", "Ethan Brooks", "CyberNova", "manual_sow_request", 6,
             "SOW review for CyberNova: 2 of 3 milestones completed. Final milestone (API integration) blocked on customer IT resources. Deadline at risk — escalated to delivery lead."),
            # Deployment Intel (Zara)
            ("deployment_intel_agent", "Zara Kim", "SecureNet", "jira_deployment_event", 8,
             "Post-deployment analysis for SecureNet v4.3. Hotfix resolved original memory leak but introduced timeout on large subnets. Correlated with 1 new ticket. Risk assessment: medium. Lesson: large subnet configs need dedicated testing."),
            ("deployment_intel_agent", "Zara Kim", "DataShield", "jira_deployment_event", 3,
             "DataShield v4.2 deployment. Clean deployment, no rollback needed. All health metrics stable post-deploy. Risk: low."),
            ("deployment_intel_agent", "Zara Kim", "Acme Corp", "jira_deployment_event", 6,
             "Acme Corp hotfix deployment for scan engine. Applied KB-2024-0312 successfully. Scan engine restarted, memory usage normalized. Monitoring for 24 hours."),
            # Support Lead (Rachel)
            ("support_lead", "Rachel Torres", "Acme Corp", "jira_ticket_created", 6,
             "Coordinated P1 resolution for Acme Corp. Triage + troubleshooting completed in 90 minutes. SLA met. Team performance: excellent. Kai's pattern matching was critical for fast triage."),
            ("support_lead", "Rachel Torres", "CyberNova", "jira_ticket_created", 9,
             "Emergency coordination for CyberNova. 4 P1 tickets investigated. 2 blocked on customer access, 1 product bug, 1 quick fix. Escalated to orchestrator for executive intervention."),
            # Value Lead (Damon)
            ("value_lead", "Damon Reeves", "TechVault", "fathom_call_recorded", 8,
             "TechVault cross-signal analysis: declining health (58), negative call sentiment (0.45), competitor evaluation detected. Coordinated call intel + health monitor for comprehensive assessment. Recommended executive outreach."),
            ("value_lead", "Damon Reeves", "DataShield", "cron_qbr_schedule", 5,
             "DataShield QBR coordination. Gathered data from call intel, health monitor, and delivery lane. Smooth cross-lane collaboration. Report highlights upsell opportunity."),
            # Orchestrator (Naveen)
            ("cso_orchestrator", "Naveen Kapoor", "CyberNova", "cron_health_check", 10,
             "CyberNova crisis management. Delegated to value lane (health analysis) and support lane (ticket resolution). Escalation triggered. Key learning: monitor customers with >3 open P1s weekly, not daily."),
            ("cso_orchestrator", "Naveen Kapoor", "Acme Corp", "jira_ticket_created", 6,
             "Standard P1 routing for Acme Corp. Support lane handled efficiently — resolved in 90 minutes. Good example of smooth Tier 1→2→3→2→1 delegation flow."),
        ]

        documents = []
        metadatas = []
        ids = []

        for agent_id, agent_name, customer, event_type, importance, content in memories:
            exec_id = str(uuid.uuid4())
            mem_id = f"ep-{agent_id}-{uuid.uuid4().hex[:8]}"
            documents.append(content)
            metadatas.append({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "customer_name": customer,
                "event_type": event_type,
                "execution_id": exec_id,
                "importance": importance,
                "tier": AGENT_TIERS[agent_id],
                "lane": AGENT_LANES[agent_id] or "none",
                "timestamp": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))).isoformat(),
            })
            ids.append(mem_id)

        episodic_memory.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"Created {len(documents)} episodic memories in ChromaDB")

    except Exception as e:
        print(f"Episodic memory seeding failed (non-fatal): {e}")


def _seed_shared_knowledge():
    """Seed 15 shared knowledge entries in ChromaDB (5 per lane)."""
    print("Seeding shared knowledge into ChromaDB...")

    try:
        from app.chromadb_client import shared_knowledge

        if shared_knowledge is None:
            print("  Skipped — shared_knowledge collection not available")
            return

        entries = [
            # Support Lane (5)
            ("triage_agent", "Kai Nakamura", "support", "pattern", 8,
             ["scan-failure", "memory-leak", "v4.2"],
             "Scan engine memory leak pattern: affects v4.2.x deployments. Symptoms appear 48-72 hours after restart. Resolution: apply hotfix KB-2024-0312 and restart. Seen in 4 customers."),
            ("troubleshooter_agent", "Leo Petrov", "support", "best_practice", 7,
             ["troubleshooting", "subnet", "timeout"],
             "When investigating scan timeouts, always check subnet size first. Subnets >500 hosts have different timeout behavior in v4.3+. Test with customer's actual subnet configuration."),
            ("escalation_agent", "Maya Santiago", "support", "pattern", 9,
             ["escalation", "churn-signal", "sla"],
             "Escalation trigger pattern: 3+ unresolved P1 tickets + declining health score + upcoming renewal = immediate executive escalation. Don't wait for SLA breach — proactive escalation saves accounts."),
            ("triage_agent", "Kai Nakamura", "support", "customer_pattern", 6,
             ["authentication", "ldap", "enterprise"],
             "Enterprise customers with LDAP integration frequently report authentication timeouts during peak hours. Root cause: connection pool exhaustion. Standard fix: increase pool size in config."),
            ("troubleshooter_agent", "Leo Petrov", "support", "best_practice", 7,
             ["deployment", "rollback", "testing"],
             "Post-deployment verification checklist: 1) Run scan on small subnet 2) Check memory usage after 1 hour 3) Verify large subnet timeout settings 4) Compare ticket volume to pre-deployment baseline."),

            # Value Lane (5)
            ("fathom_agent", "Jordan Ellis", "value", "pattern", 8,
             ["competitor", "churn-signal", "sentiment"],
             "Competitor mention correlation: when a customer mentions evaluating competitors in a call, health score drops an average of 15 points in the following 2 weeks. Immediate proactive outreach recommended."),
            ("health_monitor_agent", "Dr. Aisha Okafor", "value", "pattern", 9,
             ["health", "churn", "engagement"],
             "Churn prediction signal: zero engagement (no calls, no portal logins) for 3+ weeks combined with health score <50 predicts churn with 78% accuracy. Flag immediately for executive outreach."),
            ("qbr_agent", "Sofia Marquez", "value", "best_practice", 6,
             ["qbr", "narrative", "upsell"],
             "QBR structure that drives renewals: 1) Start with wins (resolved tickets, health improvements) 2) Acknowledge challenges honestly 3) Show product roadmap alignment with their needs 4) End with expansion opportunity."),
            ("health_monitor_agent", "Dr. Aisha Okafor", "value", "customer_pattern", 7,
             ["health", "seasonal", "year-end"],
             "Seasonal pattern: customer engagement and health scores typically dip in December (holidays) and recover in January. Don't over-react to December dips — compare YoY instead."),
            ("fathom_agent", "Jordan Ellis", "value", "pattern", 7,
             ["sentiment", "tone-shift", "risk"],
             "Tone shift detection: when a previously positive customer's sentiment drops below 0.5, there's usually an underlying issue not yet reported as a ticket. Proactive check-in within 48 hours prevents escalation."),

            # Delivery Lane (5)
            ("deployment_intel_agent", "Zara Kim", "delivery", "pattern", 8,
             ["deployment", "risk", "correlation"],
             "Deployment-ticket correlation: 60% of P1 tickets are filed within 72 hours of a deployment. Always cross-reference new tickets with recent deployment events before troubleshooting."),
            ("sow_agent", "Ethan Brooks", "delivery", "best_practice", 7,
             ["sow", "scope-creep", "change-order"],
             "Scope creep early detection: if a customer requests 2+ items not in the original SOW within a single quarter, proactively propose a change order rather than absorbing the work. Prevents timeline slippage."),
            ("deployment_intel_agent", "Zara Kim", "delivery", "customer_pattern", 6,
             ["deployment", "enterprise", "scheduling"],
             "Enterprise deployment pattern: customers with >10 subnets should schedule deployments during maintenance windows only. Weekend deployments for large environments reduce risk of cascading scan failures."),
            ("sow_agent", "Ethan Brooks", "delivery", "pattern", 7,
             ["milestone", "delay", "dependency"],
             "Milestone delay pattern: 80% of SOW delays are caused by customer IT resource availability, not HivePro execution. Build 2-week buffer into any milestone that requires customer-side infrastructure changes."),
            ("deployment_intel_agent", "Zara Kim", "delivery", "best_practice", 8,
             ["hotfix", "regression", "testing"],
             "Hotfix regression prevention: after applying any hotfix, run the full regression suite on a staging environment that mirrors the customer's subnet topology. Quick hotfixes that skip staging cause 40% of re-opened tickets."),
        ]

        documents = []
        metadatas = []
        ids = []

        for agent_id, agent_name, lane, knowledge_type, importance, tags, content in entries:
            entry_id = f"sk-{lane}-{uuid.uuid4().hex[:8]}"
            documents.append(content)
            metadatas.append({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "lane": lane,
                "tags": ",".join(tags),  # ChromaDB metadata values must be str/int/float
                "importance": importance,
                "knowledge_type": knowledge_type,
                "timestamp": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))).isoformat(),
            })
            ids.append(entry_id)

        shared_knowledge.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"Created {len(documents)} shared knowledge entries in ChromaDB")

    except Exception as e:
        print(f"Shared knowledge seeding failed (non-fatal): {e}")


def _seed_meeting_knowledge():
    """Seed the meeting_knowledge ChromaDB collection from external data files."""
    import json
    from pathlib import Path

    print("\n--- Meeting Knowledge (ChromaDB) ---")

    data_dir = Path(__file__).parent.parent.parent / "data" / "meeting_knowledge"
    metadata_path = data_dir / "vector_metadata.json"
    chunks_path = data_dir / "chunks_for_lookup.json"

    if not metadata_path.exists() or not chunks_path.exists():
        print("Meeting knowledge data files not found — skipping")
        print(f"  Expected: {metadata_path}")
        return

    try:
        from app.chromadb_client import meeting_knowledge

        if meeting_knowledge is None:
            print("ChromaDB meeting_knowledge collection unavailable — skipping")
            return

        # Check if already seeded
        existing = meeting_knowledge.count()
        if existing > 0:
            print(f"Meeting knowledge already has {existing} entries — skipping")
            return

        with open(chunks_path) as f:
            chunks_data = json.load(f)

        with open(metadata_path) as f:
            metadata_list = json.load(f)

        # Build a lookup from chunk_id to content
        chunk_content_map = {}
        for chunk in chunks_data:
            chunk_content_map[chunk["chunk_id"]] = chunk.get("content", "")

        documents = []
        metadatas = []
        ids = []

        for meta in metadata_list:
            chunk_id = meta["chunk_id"]
            content = chunk_content_map.get(chunk_id, "")
            if not content:
                continue

            documents.append(content)
            metadatas.append({
                "meeting_id": str(meta.get("meeting_id", "")),
                "meeting_title": meta.get("meeting_title", ""),
                "category": meta.get("category", ""),
                "section_type": meta.get("section_type", ""),
            })
            ids.append(str(chunk_id))

        # ChromaDB batch size limit is ~41666, but let's batch at 100 for safety
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            end = min(i + batch_size, len(documents))
            meeting_knowledge.add(
                documents=documents[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end],
            )

        print(f"Created {len(documents)} meeting knowledge chunks in ChromaDB")
        print(f"  Categories: {len(set(m['category'] for m in metadatas))}")
        print(f"  Meetings: {len(set(m['meeting_id'] for m in metadatas))}")

    except Exception as e:
        print(f"Meeting knowledge seeding failed (non-fatal): {e}")


def clear():
    """Remove all seeded demo data, preserving user accounts."""
    # Delete order: children first to respect foreign key constraints
    TABLES_TO_CLEAR = [
        "chat_messages",
        "chat_conversations",
        "agent_messages",
        "agent_execution_rounds",
        "action_items",
        "alerts",
        "reports",
        "agent_logs",
        "call_insights",
        "tickets",
        "health_scores",
        "events",
        "customers",
    ]

    with Session(engine) as session:
        counts = {}
        for table in TABLES_TO_CLEAR:
            result = session.execute(text(f"DELETE FROM {table}"))
            counts[table] = result.rowcount
        session.commit()

        print("Cleared database tables:")
        for table, count in counts.items():
            print(f"  {table}: {count} rows deleted")

    # Clear ChromaDB collections
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chromadb_data")
        for coll_name in ["ticket_embeddings", "insight_embeddings", "meeting_knowledge", "episodic_memory", "shared_knowledge"]:
            try:
                coll = client.get_collection(coll_name)
                count = coll.count()
                client.delete_collection(coll_name)
                print(f"  ChromaDB {coll_name}: {count} entries deleted")
            except Exception:
                pass
    except Exception as e:
        print(f"ChromaDB cleanup failed (non-fatal): {e}")

    print("\nDone. User accounts preserved. Database is now clean.")


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]

    if "--clear" in args:
        clear()
    elif "--demo" in args:
        seed()
    else:
        print("Usage: python -m app.utils.seed [--demo | --clear]")
        print()
        print("  --demo   Populate database with demo/seed data")
        print("  --clear  Remove all seeded data (preserves user accounts)")
        print()
        print("No flag provided. Seed data is only for demo mode.")
        print("Run with --demo to seed, or --clear to wipe existing data.")
