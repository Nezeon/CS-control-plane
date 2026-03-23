"""
Demo Logger -- Rich terminal output for CTO presentations.

Provides ANSI-colored, box-drawing-enhanced logging for pipeline execution.
Installed when DEMO_MODE=true via install_demo_formatter().
"""

import logging
import sys

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Tier colors
TEAL = "\033[38;2;0;245;212m"      # T1 Supervisor (#00F5D4)
VIOLET = "\033[38;2;139;92;246m"   # T2 Lane Leads (#8B5CF6)
CYAN = "\033[38;2;34;211;238m"     # T3 Specialists (#22D3EE)
SLATE = "\033[38;2;100;116;139m"   # T4 Foundation (#64748B)
WHITE = "\033[97m"
YELLOW = "\033[38;2;251;191;36m"   # Amber
GREEN = "\033[38;2;52;211;153m"    # Emerald
ROSE = "\033[38;2;251;113;133m"    # Rose

TIER_COLORS = {1: TEAL, 2: VIOLET, 3: CYAN, 4: SLATE}
TIER_LABELS = {1: "T1 Supervisor", 2: "T2 Lane Lead", 3: "T3 Specialist", 4: "T4 Foundation"}


def tier_color(tier: int) -> str:
    return TIER_COLORS.get(tier, WHITE)


def pipeline_header(agent_id: str, agent_name: str, tier: int, event_type: str, customer_name: str, stages: list[str]) -> str:
    """Format a pipeline start header with box drawing."""
    color = tier_color(tier)
    label = TIER_LABELS.get(tier, f"T{tier}")
    stages_str = " -> ".join(stages)

    lines = [
        "",
        f"{color}{BOLD}{'=' * 72}{RESET}",
        f"{color}{BOLD}  PIPELINE: {agent_name} ({label}){RESET}",
        f"{color}  Agent ID: {agent_id}{RESET}",
        f"{color}  Event: {event_type} | Customer: {customer_name}{RESET}",
        f"{color}  Stages: {stages_str}{RESET}",
        f"{color}{BOLD}{'=' * 72}{RESET}",
    ]
    return "\n".join(lines)


def stage_start(agent_name: str, tier: int, stage_name: str, stage_type: str, stage_num: int, total: int) -> str:
    """Format a stage start marker."""
    color = tier_color(tier)
    return (
        f"\n{color}  +--- Stage {stage_num}/{total}: {stage_name} ({stage_type}) "
        f"{'-' * max(1, 50 - len(stage_name) - len(stage_type))}{RESET}"
        f"\n{color}  |  Agent: {agent_name}{RESET}"
    )


def stage_complete(tier: int, stage_name: str, duration_ms: int) -> str:
    """Format a stage completion marker."""
    color = tier_color(tier)
    duration_str = f"{duration_ms}ms" if duration_ms < 1000 else f"{duration_ms / 1000:.1f}s"
    return f"{color}  +--- Completed: {stage_name} in {GREEN}{duration_str}{RESET}"


def claude_call_start(agent_name: str, prompt_chars: int) -> str:
    """Format a Claude API call start."""
    return f"{YELLOW}  |  >> Claude API call ({prompt_chars:,} chars prompt){RESET}"


def claude_call_done(content_chars: int, duration_ms: int, input_tokens: int = 0, output_tokens: int = 0) -> str:
    """Format a Claude API call completion."""
    duration_str = f"{duration_ms}ms" if duration_ms < 1000 else f"{duration_ms / 1000:.1f}s"
    token_str = ""
    if input_tokens or output_tokens:
        token_str = f" (in: {input_tokens:,} / out: {output_tokens:,} tokens)"
    return f"{GREEN}  |  << Claude responded: {content_chars:,} chars in {duration_str}{token_str}{RESET}"


def claude_call_error(error_msg: str, duration_ms: int) -> str:
    """Format a Claude API call error."""
    return f"{ROSE}  |  !! Claude error in {duration_ms}ms: {error_msg[:200]}{RESET}"


def pipeline_complete(agent_name: str, tier: int, status: str, duration_ms: int, stages_count: int) -> str:
    """Format a pipeline completion summary."""
    color = tier_color(tier)
    duration_str = f"{duration_ms}ms" if duration_ms < 1000 else f"{duration_ms / 1000:.1f}s"
    status_color = GREEN if status == "completed" else ROSE
    return (
        f"\n{color}{BOLD}  >> Pipeline done: {agent_name} | "
        f"{status_color}{status}{RESET}{color}{BOLD} | "
        f"{stages_count} stages in {duration_str}{RESET}\n"
    )


def delegation_start(from_name: str, to_name: str, lane: str) -> str:
    """Format a delegation event."""
    return (
        f"\n{VIOLET}{BOLD}  >>> DELEGATING to {lane.upper()} lane: {to_name}{RESET}"
        f"\n{VIOLET}  |   From: {from_name}{RESET}"
    )


def delegation_complete(lane: str, success: bool) -> str:
    """Format a delegation completion."""
    status_color = GREEN if success else ROSE
    status_str = "SUCCESS" if success else "FAILED"
    return f"{VIOLET}{BOLD}  <<< {lane.upper()} lane: {status_color}{status_str}{RESET}"


def email_draft_display(draft_email: str) -> str:
    """Format the generated email draft prominently in terminal."""
    border = f"{TEAL}{'=' * 72}{RESET}"
    lines = [
        "",
        border,
        f"{TEAL}{BOLD}  GENERATED EMAIL DRAFT (ready for review){RESET}",
        border,
        f"{WHITE}{draft_email}{RESET}",
        border,
        "",
    ]
    return "\n".join(lines)


def result_summary(result: dict) -> str:
    """Format the final result summary."""
    output = result.get("output", {})
    success = result.get("success", False)
    reasoning = result.get("reasoning_summary", "")

    status_color = GREEN if success else ROSE
    lines = [
        "",
        f"{BOLD}{'-' * 72}{RESET}",
        f"{BOLD}  FINAL RESULT: {status_color}{'SUCCESS' if success else 'FAILED'}{RESET}",
        f"{DIM}  {reasoning[:200]}{RESET}",
    ]

    # Show email draft if present
    draft = _find_draft_email(output)
    if draft:
        lines.append(email_draft_display(draft))

    lines.append(f"{BOLD}{'-' * 72}{RESET}")
    return "\n".join(lines)


def _find_draft_email(output: dict, depth: int = 0) -> str | None:
    """Recursively search for draft_email in nested output."""
    if depth > 5 or not isinstance(output, dict):
        return None
    if "draft_email" in output:
        return output["draft_email"]
    for key in ("output", "deliverables", "specialist_outputs"):
        nested = output.get(key, {})
        if isinstance(nested, dict):
            for v in nested.values() if key != "output" else [nested]:
                found = _find_draft_email(v if isinstance(v, dict) else {}, depth + 1)
                if found:
                    return found
    return None


class DemoFormatter(logging.Formatter):
    """Custom formatter that applies tier colors to pipeline/agent log messages."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # Add subtle timestamp prefix
        return f"{DIM}{record.asctime}{RESET} {msg}" if hasattr(record, "asctime") else msg


def install_demo_formatter():
    """Install rich demo formatting on pipeline and agent loggers."""
    # Ensure stdout supports Unicode on Windows (cp1252 workaround)
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    formatter = DemoFormatter(fmt="%(message)s", datefmt="%H:%M:%S")

    # Configure root handler for pipeline and agent loggers
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)

    logger_names = [
        "pipeline_engine",
        "agents",
        "agents.orchestrator",
        "agents.triage_agent",
        "agents.health_monitor",
        "agents.customer_memory",
    ]

    for name in logger_names:
        lgr = logging.getLogger(name)
        lgr.handlers = [handler]
        lgr.setLevel(logging.DEBUG)
        lgr.propagate = False
