"""
Message Service — Business logic for inter-agent communication.

Provides sync send methods (for agents in Celery tasks) and async query methods
(for FastAPI routers). Auto-resolves agent names and message direction from
ProfileLoader YAML config.
"""

import logging
import uuid
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.profile_loader import ProfileLoader
from app.models.agent_message import AgentMessage
from app.models.customer import Customer

logger = logging.getLogger("services.message")


class MessageService:

    # ── Direction Resolution ──────────────────────────────────────

    def _resolve_direction(self, from_agent: str, to_agent: str) -> str:
        """Determine direction based on tier comparison."""
        loader = ProfileLoader.get()
        from_profile = loader.get_agent_profile(from_agent) or {}
        to_profile = loader.get_agent_profile(to_agent) or {}
        from_tier = from_profile.get("tier", 3)
        to_tier = to_profile.get("tier", 3)

        if from_tier < to_tier:
            return "down"
        elif from_tier > to_tier:
            return "up"
        else:
            return "sideways"

    def _resolve_name(self, agent_id: str) -> str:
        """Get display name for an agent from YAML profile."""
        loader = ProfileLoader.get()
        profile = loader.get_agent_profile(agent_id) or {}
        return profile.get("name", agent_id)

    # ── Send Methods (sync — for Celery tasks / agents) ───────────

    def send_message(
        self,
        db_session,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: str,
        priority: int = 5,
        event_id: UUID | None = None,
        customer_id: UUID | None = None,
        thread_id: UUID | None = None,
        parent_id: UUID | None = None,
        execution_id: UUID | None = None,
    ) -> AgentMessage:
        """
        Core send method. Creates an AgentMessage record.
        Direction and names are auto-resolved from ProfileLoader.
        """
        direction = self._resolve_direction(from_agent, to_agent)

        msg = AgentMessage(
            id=uuid.uuid4(),
            thread_id=thread_id,
            parent_id=parent_id,
            from_agent=from_agent,
            from_name=self._resolve_name(from_agent),
            to_agent=to_agent,
            to_name=self._resolve_name(to_agent),
            message_type=message_type,
            direction=direction,
            content=content,
            priority=max(1, min(10, priority)),
            event_id=event_id,
            execution_id=execution_id,
            customer_id=customer_id,
            status="pending",
        )

        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        # For task_assignment, set thread_id = own id if not provided
        if message_type == "task_assignment" and thread_id is None:
            msg.thread_id = msg.id
            db_session.commit()

        logger.info(
            f"Message sent: {from_agent} → {to_agent} "
            f"(type={message_type}, direction={direction}, id={msg.id})"
        )
        return msg

    def send_task_assignment(
        self,
        db_session,
        from_agent: str,
        to_agent: str,
        content: str,
        priority: int = 5,
        event_id: UUID | None = None,
        customer_id: UUID | None = None,
        execution_id: UUID | None = None,
    ) -> AgentMessage:
        """Send a task assignment (typically down the hierarchy)."""
        return self.send_message(
            db_session=db_session,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type="task_assignment",
            content=content,
            priority=priority,
            event_id=event_id,
            customer_id=customer_id,
            execution_id=execution_id,
        )

    def send_deliverable(
        self,
        db_session,
        from_agent: str,
        to_agent: str,
        thread_id: UUID,
        content: str,
        priority: int = 5,
        event_id: UUID | None = None,
        customer_id: UUID | None = None,
        execution_id: UUID | None = None,
        parent_id: UUID | None = None,
    ) -> AgentMessage:
        """Send a deliverable (typically up the hierarchy)."""
        return self.send_message(
            db_session=db_session,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type="deliverable",
            content=content,
            priority=priority,
            event_id=event_id,
            customer_id=customer_id,
            thread_id=thread_id,
            parent_id=parent_id,
            execution_id=execution_id,
        )

    def send_escalation(
        self,
        db_session,
        from_agent: str,
        to_agent: str,
        content: str,
        priority: int = 8,
        event_id: UUID | None = None,
        customer_id: UUID | None = None,
        execution_id: UUID | None = None,
    ) -> AgentMessage:
        """Send an escalation (always up to higher tier). Priority defaults to 8."""
        return self.send_message(
            db_session=db_session,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type="escalation",
            content=content,
            priority=max(priority, 7),  # Escalations are always high priority
            event_id=event_id,
            customer_id=customer_id,
            execution_id=execution_id,
        )

    def send_feedback(
        self,
        db_session,
        from_agent: str,
        to_agent: str,
        thread_id: UUID,
        content: str,
        priority: int = 5,
        event_id: UUID | None = None,
        customer_id: UUID | None = None,
        execution_id: UUID | None = None,
    ) -> AgentMessage:
        """Send feedback (typically down the hierarchy, within a thread)."""
        return self.send_message(
            db_session=db_session,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type="feedback",
            content=content,
            priority=priority,
            event_id=event_id,
            customer_id=customer_id,
            thread_id=thread_id,
            execution_id=execution_id,
        )

    # ── Query Methods (async — for FastAPI routers) ───────────────

    async def list_messages(
        self,
        db: AsyncSession,
        message_type: str | None = None,
        agent_id: str | None = None,
        event_id: UUID | None = None,
        lane: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list, int]:
        """List messages with optional filters. Returns (rows, total_count)."""
        base_query = select(AgentMessage, Customer.name.label("customer_name")).outerjoin(
            Customer, AgentMessage.customer_id == Customer.id
        )
        count_query = select(func.count()).select_from(AgentMessage)

        # Apply filters
        filters = []
        if message_type:
            filters.append(AgentMessage.message_type == message_type)
        if agent_id:
            filters.append(
                or_(AgentMessage.from_agent == agent_id, AgentMessage.to_agent == agent_id)
            )
        if event_id:
            filters.append(AgentMessage.event_id == event_id)
        if lane:
            # Filter by agents in a lane
            loader = ProfileLoader.get()
            lane_agents = loader.get_agents_in_lane(lane)
            if lane_agents:
                filters.append(
                    or_(
                        AgentMessage.from_agent.in_(lane_agents),
                        AgentMessage.to_agent.in_(lane_agents),
                    )
                )

        for f in filters:
            base_query = base_query.where(f)
            count_query = count_query.where(f)

        # Total
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Fetch
        result = await db.execute(
            base_query.order_by(AgentMessage.created_at.desc()).offset(offset).limit(limit)
        )
        rows = result.all()

        return rows, total

    async def get_thread(self, db: AsyncSession, thread_id: UUID) -> list:
        """Get all messages in a thread, ordered chronologically."""
        result = await db.execute(
            select(AgentMessage, Customer.name.label("customer_name"))
            .outerjoin(Customer, AgentMessage.customer_id == Customer.id)
            .where(AgentMessage.thread_id == thread_id)
            .order_by(AgentMessage.created_at.asc())
        )
        return result.all()

    async def get_agent_messages(
        self,
        db: AsyncSession,
        agent_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list, int]:
        """Get messages sent to or from a specific agent."""
        agent_filter = or_(
            AgentMessage.from_agent == agent_id, AgentMessage.to_agent == agent_id
        )

        count_result = await db.execute(
            select(func.count()).select_from(AgentMessage).where(agent_filter)
        )
        total = count_result.scalar() or 0

        result = await db.execute(
            select(AgentMessage, Customer.name.label("customer_name"))
            .outerjoin(Customer, AgentMessage.customer_id == Customer.id)
            .where(agent_filter)
            .order_by(AgentMessage.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.all(), total

    async def get_event_messages(self, db: AsyncSession, event_id: UUID) -> list:
        """Get all messages related to a specific event."""
        result = await db.execute(
            select(AgentMessage, Customer.name.label("customer_name"))
            .outerjoin(Customer, AgentMessage.customer_id == Customer.id)
            .where(AgentMessage.event_id == event_id)
            .order_by(AgentMessage.created_at.asc())
        )
        return result.all()

    async def mark_read(self, db: AsyncSession, message_id: UUID) -> None:
        """Mark a message as read."""
        result = await db.execute(
            select(AgentMessage).where(AgentMessage.id == message_id)
        )
        msg = result.scalar_one_or_none()
        if msg:
            msg.status = "read"
            await db.commit()

    async def mark_completed(self, db: AsyncSession, message_id: UUID) -> None:
        """Mark a message as completed."""
        result = await db.execute(
            select(AgentMessage).where(AgentMessage.id == message_id)
        )
        msg = result.scalar_one_or_none()
        if msg:
            msg.status = "completed"
            await db.commit()


# Singleton
message_service = MessageService()
