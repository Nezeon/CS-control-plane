"""
Markdown-to-Slack Block Kit converter.

Converts the markdown responses produced by the chat pipeline (fast path /
agent pipeline) into Slack Block Kit blocks for rich message rendering.
"""

import re

# Slack limits
MAX_BLOCK_TEXT = 3000
MAX_BLOCKS = 50
MAX_HEADER_TEXT = 150


def format_slack_blocks(markdown_text: str) -> list[dict]:
    """Convert a markdown response into Slack Block Kit blocks.

    Handles headings, bold, bullet lists, and plain paragraphs.
    Returns a list of Block Kit block dicts ready for ``chat.postMessage``.
    """
    if not markdown_text:
        return []

    blocks: list[dict] = []
    lines = markdown_text.split("\n")
    buffer: list[str] = []

    def flush_buffer():
        if not buffer:
            return
        text = "\n".join(buffer).strip()
        if not text:
            buffer.clear()
            return
        text = _md_to_mrkdwn(text)
        # Split oversized blocks instead of truncating
        while len(text) > MAX_BLOCK_TEXT:
            split_at = text.rfind("\n", 0, MAX_BLOCK_TEXT)
            if split_at == -1:
                split_at = MAX_BLOCK_TEXT
            blocks.append(_section_block(text[:split_at]))
            text = text[split_at:].lstrip()
        if text:
            blocks.append(_section_block(text))
        buffer.clear()

    for line in lines:
        if len(blocks) >= MAX_BLOCKS - 1:
            flush_buffer()
            break

        stripped = line.strip()

        # Headings -> header blocks
        heading_match = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading_match:
            flush_buffer()
            heading_text = heading_match.group(2).strip()[:MAX_HEADER_TEXT]
            blocks.append({
                "type": "header",
                "text": {"type": "plain_text", "text": heading_text, "emoji": True},
            })
            continue

        # Horizontal rules -> dividers
        if re.match(r"^[-*_]{3,}$", stripped):
            flush_buffer()
            blocks.append({"type": "divider"})
            continue

        # Everything else accumulates in the buffer
        buffer.append(line)

    flush_buffer()

    # Cap at MAX_BLOCKS
    return blocks[:MAX_BLOCKS]


def plain_text_fallback(markdown_text: str) -> str:
    """Strip markdown formatting for the ``text`` fallback parameter."""
    if not markdown_text:
        return ""
    text = markdown_text
    # Strip heading markers
    text = re.sub(r"^#{1,3}\s+", "", text, flags=re.MULTILINE)
    # Bold **text** -> text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    # Inline code
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text[:3000]


# ── Internal helpers ─────────────────────────────────────────────────────


def _md_to_mrkdwn(text: str) -> str:
    """Convert common markdown to Slack mrkdwn dialect."""
    # **bold** -> *bold*
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)
    # [link text](url) -> <url|link text>
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<\2|\1>", text)
    return text[:MAX_BLOCK_TEXT]


def _section_block(text: str) -> dict:
    """Create a section block with mrkdwn text."""
    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": text[:MAX_BLOCK_TEXT]},
    }
