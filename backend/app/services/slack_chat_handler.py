"""
Slack Chat Handler — Processes inbound Slack messages through the existing
chat pipeline and posts responses back as threaded replies.

Handles signature verification, event deduplication, Slack-user-to-system-user
mapping, and conversation threading (Slack thread_ts <-> ChatConversation).
"""

import hashlib
import hmac
import logging
import time
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger("services.slack_chat")

# Dedup cache TTL in seconds
_DEDUP_TTL = 300  # 5 minutes


class SlackChatHandler:
    """Orchestrates inbound Slack messages through the chat pipeline."""

    def __init__(self):
        self._seen_events: dict[str, float] = {}  # event_id -> timestamp
        self._slack_user_id_cache: uuid.UUID | None = None

    # ── Signature Verification ───────────────────────────────────────────

    def verify_signature(self, timestamp: str, body: bytes, signature: str) -> bool:
        """Verify a Slack request signature (HMAC-SHA256).

        Slack signs requests as ``v0=HMAC-SHA256(signing_secret, "v0:{ts}:{body}")``.
        Rejects requests older than 5 minutes to prevent replay attacks.
        """
        secret = settings.SLACK_SIGNING_SECRET
        if not secret:
            logger.warning("[SlackChat] No SLACK_SIGNING_SECRET configured, skipping verification")
            return True  # Allow in dev if not configured

        # Replay protection
        try:
            if abs(time.time() - int(timestamp)) > 300:
                logger.warning("[SlackChat] Request timestamp too old")
                return False
        except (ValueError, TypeError):
            return False

        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        expected = "v0=" + hmac.new(
            secret.encode("utf-8"),
            sig_basestring.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    # ── Event Deduplication ──────────────────────────────────────────────

    def is_duplicate(self, event_id: str) -> bool:
        """Check if we've already processed this Slack event (retry protection)."""
        self._evict_stale()
        if event_id in self._seen_events:
            return True
        self._seen_events[event_id] = time.time()
        return False

    def _evict_stale(self):
        """Remove dedup entries older than TTL."""
        cutoff = time.time() - _DEDUP_TTL
        stale = [k for k, v in self._seen_events.items() if v < cutoff]
        for k in stale:
            del self._seen_events[k]

    # ── User Mapping ─────────────────────────────────────────────────────

    def get_or_create_slack_user(self, db: Session) -> uuid.UUID:
        """Get or create the shared ``slack-bot@hivepro.com`` system user.

        All Slack interactions run under this single user.  The actual Slack
        user's name/ID is stored in ``ChatConversation.metadata_``.
        """
        if self._slack_user_id_cache:
            logger.info("[SlackChat] System user: cache hit")
            return self._slack_user_id_cache

        from app.models.user import User

        user = db.query(User).filter_by(email="slack-bot@hivepro.com").first()
        if not user:
            from passlib.context import CryptContext
            pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

            user = User(
                id=uuid.uuid4(),
                email="slack-bot@hivepro.com",
                hashed_password=pwd_ctx.hash(uuid.uuid4().hex),
                full_name="Slack Bot",
                role="system",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"[SlackChat] Created system user slack-bot@hivepro.com (id={user.id})")

        self._slack_user_id_cache = user.id
        return user.id

    # ── Conversation Threading ───────────────────────────────────────────

    def find_or_create_conversation(
        self,
        db: Session,
        channel: str,
        thread_ts: str,
        user_id: uuid.UUID,
        slack_user_name: str,
        text: str,
    ) -> uuid.UUID:
        """Map a Slack thread to a ChatConversation.

        Looks up an existing conversation by ``slack_thread_ts`` in the JSONB
        ``metadata_`` column. Creates a new one if none exists.
        """
        from sqlalchemy import cast, String
        from app.models.chat_conversation import ChatConversation

        # Search for existing conversation with this thread_ts
        existing = (
            db.query(ChatConversation)
            .filter(
                ChatConversation.metadata_["slack_thread_ts"].as_string() == thread_ts,
                ChatConversation.status == "active",
            )
            .first()
        )

        if existing:
            logger.info(f"[SlackChat] Conversation: found existing {existing.id} for thread {thread_ts}")
            return existing.id

        # Create new conversation
        conv = ChatConversation(
            id=uuid.uuid4(),
            user_id=user_id,
            title=text[:60] if text else "Slack conversation",
            metadata_={
                "slack_channel": channel,
                "slack_thread_ts": thread_ts,
                "slack_user_name": slack_user_name,
                "source": "slack",
            },
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        logger.info(f"[SlackChat] Created conversation {conv.id} for thread {thread_ts}")
        return conv.id

    # ── Main Handler (runs in background thread) ─────────────────────────

    def handle_message(
        self,
        channel: str,
        slack_user_id: str,
        slack_user_name: str,
        text: str,
        thread_ts: str,
        event_id: str,
    ) -> None:
        """Process a Slack message through the chat pipeline and post the response.

        This method runs in a background thread (via ``run_in_executor``).
        It reuses ``ChatService.process_message_full()`` which handles the full
        classify -> memory -> fast-path/pipeline -> save flow.
        """
        from app.database import get_sync_session
        from app.services.chat_service import chat_service
        from app.models.chat_message import ChatMessage

        logger.info(
            f"[SlackChat] Processing message from {slack_user_name} in {channel}: "
            f"{text[:80]}..."
        )

        db = get_sync_session()
        try:
            # 1. Resolve system user
            logger.info("[SlackChat] Step 1: Resolving system user...")
            system_user_id = self.get_or_create_slack_user(db)

            # 2. Find or create conversation mapped to Slack thread
            logger.info(f"[SlackChat] Step 2: Mapping Slack thread {thread_ts} to conversation...")
            conversation_id = self.find_or_create_conversation(
                db, channel, thread_ts, system_user_id, slack_user_name, text,
            )
            db.close()

            # 3. Generate UUIDs for the message pair
            message_id = uuid.uuid4()
            assistant_msg_id = uuid.uuid4()
            logger.info(f"[SlackChat] Step 3: Message IDs — user={message_id}, assistant={assistant_msg_id}")

            # 4. Run through the existing chat pipeline
            logger.info("[SlackChat] Step 4: Calling process_message_full()...")
            chat_service.process_message_full(
                user_id_str=str(system_user_id),
                message=text,
                customer_id_str=None,
                conversation_id_str=str(conversation_id),
                message_id_str=str(message_id),
                assistant_msg_id_str=str(assistant_msg_id),
            )

            # 5. Read the completed assistant message
            logger.info("[SlackChat] Step 5: Reading completed assistant message...")
            db2 = get_sync_session()
            try:
                assistant_msg = db2.query(ChatMessage).filter_by(id=assistant_msg_id).first()
                content = assistant_msg.content if assistant_msg else "I couldn't generate a response."
                logger.info(
                    f"[SlackChat] Message readback: status={assistant_msg.pipeline_status if assistant_msg else 'NOT_FOUND'}, "
                    f"content_length={len(content)}"
                )

                if assistant_msg and assistant_msg.pipeline_status == "failed":
                    content = f"Sorry, I encountered an error processing your request.\n\n{content}"
            finally:
                db2.close()

            # 6. Post response back to Slack as a threaded reply
            logger.info("[SlackChat] Step 6: Formatting and posting to Slack...")
            self.post_response(channel, thread_ts, content)

        except Exception as e:
            logger.error(f"[SlackChat] Error processing message: {e}", exc_info=True)
            # Try to post an error message back to Slack
            try:
                self.post_response(
                    channel, thread_ts,
                    "Sorry, I encountered an error processing your request. Please try again.",
                )
            except Exception:
                logger.error("[SlackChat] Failed to post error message to Slack")
        finally:
            try:
                db.close()
            except Exception:
                pass

    # ── Teachable Rules Handler ────────────────────────────────────────────

    def handle_rule(
        self,
        channel: str,
        slack_user_id: str,
        slack_user_name: str,
        text: str,
        thread_ts: str,
    ) -> None:
        """Parse and store a teachable rule from Slack.

        Supports:
          Rule: <text>                     → global rule
          Rule for <customer>: <text>      → customer-specific rule
        """
        import re
        import uuid
        from app.database import get_sync_session
        from app.models.teachable_rule import TeachableRule

        # Strip "rule:" prefix (case-insensitive)
        rule_body = re.sub(r'^rule:\s*', '', text, flags=re.IGNORECASE).strip()
        if not rule_body:
            self.post_response(channel, thread_ts, "Please provide a rule after `Rule:`")
            return

        # Check for customer-specific pattern: "for <customer>: <rule text>"
        customer_id = None
        customer_name = None
        scope_match = re.match(r'^for\s+(.+?):\s*(.+)$', rule_body, re.IGNORECASE | re.DOTALL)
        if scope_match:
            candidate_name = scope_match.group(1).strip()
            rule_text = scope_match.group(2).strip()

            # Try to resolve customer
            db = get_sync_session()
            try:
                from app.services.chat_service import _try_resolve_customer
                customer_id, customer_name = _try_resolve_customer(db, candidate_name)
            finally:
                db.close()

            if not customer_id:
                # Couldn't find customer — save as global, warn user
                rule_text = rule_body  # Use the full text including "for X:" as context
        else:
            rule_text = rule_body

        # Save to database
        db = get_sync_session()
        try:
            rule = TeachableRule(
                id=uuid.uuid4(),
                rule_text=rule_text,
                customer_id=customer_id,
                created_by_slack_user=slack_user_id,
                created_by_name=slack_user_name,
            )
            db.add(rule)
            db.commit()

            # Post confirmation
            if customer_id:
                msg = f":white_check_mark: Rule saved for *{customer_name}*: _{rule_text}_"
            elif scope_match and not customer_id:
                msg = f":white_check_mark: Rule saved (global — couldn't find customer '{candidate_name}'): _{rule_text}_"
            else:
                msg = f":white_check_mark: Rule saved (global): _{rule_text}_"

            self.post_response(channel, thread_ts, msg)
            logger.info(f"[SlackChat] Rule saved: customer={customer_name or 'global'}, text={rule_text[:80]}")
        except Exception as e:
            db.rollback()
            logger.error(f"[SlackChat] Failed to save rule: {e}", exc_info=True)
            self.post_response(channel, thread_ts, f":x: Failed to save rule: {str(e)[:100]}")
        finally:
            db.close()

    def handle_list_rules(self, channel: str, thread_ts: str) -> None:
        """List all active teachable rules and post to Slack."""
        from app.database import get_sync_session
        from app.models.teachable_rule import TeachableRule
        from sqlalchemy import desc

        db = get_sync_session()
        try:
            rules = db.query(TeachableRule).filter(
                TeachableRule.is_active == True
            ).order_by(desc(TeachableRule.created_at)).limit(30).all()

            if not rules:
                self.post_response(channel, thread_ts, "No teachable rules saved yet.")
                return

            lines = ["*Active Teachable Rules:*\n"]
            for i, r in enumerate(rules, 1):
                scope = f"*{r.customer.name}*" if r.customer_id and r.customer else "Global"
                short_id = str(r.id)[:8]
                lines.append(f"{i}. [{scope}] {r.rule_text}  (`{short_id}`)")

            self.post_response(channel, thread_ts, "\n".join(lines))
        finally:
            db.close()

    def handle_delete_rule(self, channel: str, thread_ts: str, rule_id_prefix: str) -> None:
        """Soft-delete a teachable rule by ID prefix."""
        from app.database import get_sync_session
        from app.models.teachable_rule import TeachableRule

        db = get_sync_session()
        try:
            rule = db.query(TeachableRule).filter(
                TeachableRule.is_active == True,
                TeachableRule.id.cast(sa.String).like(f"{rule_id_prefix}%"),
            ).first()

            if not rule:
                self.post_response(channel, thread_ts, f":x: No active rule found matching `{rule_id_prefix}`")
                return

            rule.is_active = False
            db.commit()
            self.post_response(channel, thread_ts, f":white_check_mark: Rule deleted: _{rule.rule_text[:80]}_")
        except Exception as e:
            db.rollback()
            logger.error(f"[SlackChat] Failed to delete rule: {e}")
            self.post_response(channel, thread_ts, f":x: Failed to delete rule: {str(e)[:100]}")
        finally:
            db.close()

    # ── Response Posting ─────────────────────────────────────────────────

    def post_response(self, channel: str, thread_ts: str, content: str) -> bool:
        """Format and post a response back to Slack as a threaded reply."""
        from app.services.slack_service import slack_service
        from app.services.slack_formatter import format_slack_blocks, plain_text_fallback

        blocks = format_slack_blocks(content)
        fallback = plain_text_fallback(content)
        logger.info(f"[SlackChat] Formatting: {len(blocks)} blocks, {len(fallback)} char fallback")

        result = slack_service.send_message(
            channel=channel,
            text=fallback,
            blocks=blocks if blocks else None,
            thread_ts=thread_ts,
        )

        if result:
            logger.info(f"[SlackChat] Response posted to {channel} thread {thread_ts}")
            return True
        else:
            logger.error(f"[SlackChat] Failed to post response to {channel}")
            return False


# Module-level singleton
slack_chat_handler = SlackChatHandler()
