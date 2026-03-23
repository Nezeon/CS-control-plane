"""
Agent package — imports all agent modules to trigger AgentFactory registration.
"""

from app.agents.agent_factory import AgentFactory
from app.agents.base_agent import BaseAgent
from app.agents.pipeline_engine import PipelineEngine

# Tier 3 Specialists (import triggers AgentFactory.register)
from app.agents.health_monitor import HealthMonitorAgent
from app.agents.triage_agent import TicketTriageAgent
from app.agents.troubleshoot_agent import TroubleshootAgent
from app.agents.escalation_agent import EscalationAgent
from app.agents.qbr_agent import QBRAgent
from app.agents.sow_agent import SOWAgent
from app.agents.deployment_intel_agent import DeploymentIntelAgent

# Foundation
from app.agents.memory_agent import CustomerMemoryAgent

# Orchestrator
from app.agents.orchestrator import Orchestrator, orchestrator
