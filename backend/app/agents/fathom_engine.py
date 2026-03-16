"""
Fathom Engine — LangGraph-based agentic RAG for meeting knowledge retrieval.

Adapted from the HivePro-Customer-Support-Bot (agent.py).
Uses Claude (not OpenAI) and ChromaDB (not FAISS) while preserving the
multi-strategy retrieval architecture:

  1. Agent node decides which retrieval tools to call
  2. Tools node executes retrieval against ChromaDB meeting_knowledge collection
  3. Router decides: loop (more tools) or synthesize final answer
  4. Final synthesis with anonymization

Max tool calls per query: configurable (default 5).
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import TypedDict

from app.config import settings
from app.services.meeting_knowledge_service import meeting_knowledge_service

logger = logging.getLogger("agents.fathom_engine")


# ── State Definition ──────────────────────────────────────────────────────

class FathomState(TypedDict):
    query: str
    messages: list[dict]
    tool_results: list[dict]
    tool_call_count: int
    conversation_history: list[dict]
    final_answer: str | None


# ── Tool Definitions (for Claude tool_use) ────────────────────────────────

RETRIEVAL_TOOLS = [
    {
        "name": "semantic_search",
        "description": "Search the meeting knowledge base using semantic similarity. Best for general questions about platform features, past issues, or broad topics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "top_k": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "filter_by_category",
        "description": "Search within a specific meeting category. Categories: 'Problem Resolution', 'Deployment and Integration', 'Product Demonstration', 'Strategic Planning and Review', 'Enablement and Training'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Meeting category to filter by"},
                "query": {"type": "string", "description": "Search query within the category"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["category", "query"],
        },
    },
    {
        "name": "search_by_section_type",
        "description": "Search within a specific section type of meetings. Section types: 'purpose' (meeting intent), 'key_takeaways' (main points), 'topics' (subjects covered), 'next_steps' (action items and follow-ups).",
        "input_schema": {
            "type": "object",
            "properties": {
                "section_type": {"type": "string", "description": "Section type to filter"},
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["section_type", "query"],
        },
    },
    {
        "name": "filter_by_customer",
        "description": "Find meeting records related to a specific customer. Use this for internal context about a customer's history. Note: customer names must be anonymized in final responses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "Customer name to search for"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["customer_name"],
        },
    },
    {
        "name": "get_meeting_details",
        "description": "Retrieve all content chunks from a specific meeting by its ID. Use when you need the full context of a particular meeting.",
        "input_schema": {
            "type": "object",
            "properties": {
                "meeting_id": {"type": "string", "description": "The meeting ID (e.g., 'M001')"},
            },
            "required": ["meeting_id"],
        },
    },
    {
        "name": "search_fathom_api",
        "description": "Search the live Fathom API for recent meetings when the knowledge base doesn't have enough information. Use this as a LAST RESORT after trying other retrieval tools first. This queries the real Fathom recording platform.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for in meeting titles and summaries"},
                "days_back": {"type": "integer", "description": "How many days back to search (default 30)", "default": 30},
            },
            "required": ["query"],
        },
    },
]


# ── System Prompt ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Jordan Ellis, the Fathom Agent. You are an expert at answering \
questions about the HivePro platform by retrieving and synthesizing information from \
past customer meetings stored in a knowledge base and the live Fathom API.

RETRIEVAL STRATEGY:
- For general questions, start with semantic_search
- For troubleshooting/issues, use filter_by_category with "Problem Resolution"
- For deployment questions, use filter_by_category with "Deployment and Integration"
- For action items or follow-ups, use search_by_section_type with "next_steps"
- For meeting summaries, use search_by_section_type with "key_takeaways"
- For customer-specific context (internal use), use filter_by_customer
- For full meeting context, use get_meeting_details with a meeting ID
- If the knowledge base tools return insufficient results, use search_fathom_api as a LAST RESORT to query the live Fathom API for recent recordings

IMPORTANT RULES:
1. ALWAYS anonymize customer names in your responses. Use "a customer" or "a client" instead.
2. You can call up to 5 retrieval tools per query. Use as many as needed for thorough answers.
3. If initial results are insufficient, try different search strategies before resorting to search_fathom_api.
4. Base your answers ONLY on retrieved information. Never fabricate meeting content.
5. When mentioning third-party tools (Azure, ServiceNow, AWS, Splunk), provide relevant context.
6. Be concise, technical, and actionable in your responses.

RESPONSE FORMAT:
Provide a clear, structured answer based on the retrieved meeting knowledge. Include:
- Direct answer to the question
- Supporting evidence from meeting records
- Relevant action items or next steps if applicable"""


class FathomEngine:
    """LangGraph-style engine for agentic RAG over meeting knowledge."""

    def __init__(self):
        self.max_tool_calls = settings.FATHOM_MAX_TOOL_CALLS

    def run(self, query: str, conversation_history: list[dict] | None = None) -> dict:
        """
        Execute the agentic RAG pipeline.

        Returns dict with: answer, tool_calls_made, sources
        """
        state: FathomState = {
            "query": query,
            "messages": [],
            "tool_results": [],
            "tool_call_count": 0,
            "conversation_history": conversation_history or [],
            "final_answer": None,
        }

        # Check if knowledge base has data
        stats = meeting_knowledge_service.get_collection_stats()
        if stats["count"] == 0:
            return {
                "answer": "The meeting knowledge base is currently empty. No past meeting records are available to search.",
                "tool_calls_made": 0,
                "sources": [],
            }

        # Run agent loop
        max_iterations = self.max_tool_calls + 2  # safety bound
        for _ in range(max_iterations):
            # Agent decides what to do
            state = self._agent_node(state)

            if state["final_answer"] is not None:
                break

            # Execute tools
            state = self._tools_node(state)

            if state["tool_call_count"] >= self.max_tool_calls:
                # Force final synthesis
                state = self._force_synthesis(state)
                break

        return {
            "answer": state["final_answer"] or "I was unable to find relevant information in the meeting knowledge base.",
            "tool_calls_made": state["tool_call_count"],
            "sources": self._extract_sources(state["tool_results"]),
        }

    def _agent_node(self, state: FathomState) -> FathomState:
        """Claude decides whether to call tools or produce final answer."""
        from app.services import claude_service

        messages = self._build_messages(state)

        try:
            response = claude_service.call_claude(
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=RETRIEVAL_TOOLS,
                max_tokens=2048,
                temperature=0.3,
            )
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            state["final_answer"] = f"I encountered an error while processing your query: {e}"
            return state

        # Parse response
        if not response or not response.content:
            state["final_answer"] = "I was unable to generate a response."
            return state

        tool_calls = []
        text_parts = []

        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
            elif block.type == "text":
                text_parts.append(block.text)

        if tool_calls:
            # Agent wants to call tools
            state["messages"].append({
                "role": "assistant",
                "content": response.content,
            })
            state["_pending_tool_calls"] = tool_calls
        else:
            # Agent is done — text is the final answer
            state["final_answer"] = "\n".join(text_parts).strip()

        return state

    def _tools_node(self, state: FathomState) -> FathomState:
        """Execute pending tool calls."""
        pending = state.pop("_pending_tool_calls", [])

        tool_result_blocks = []
        for tc in pending:
            result = self._execute_tool(tc["name"], tc["input"])
            state["tool_results"].append({
                "tool": tc["name"],
                "input": tc["input"],
                "result": result,
            })
            state["tool_call_count"] += 1

            # Format as tool_result for Claude
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": tc["id"],
                "content": json.dumps(result, default=str)[:4000],
            })

            logger.info(f"Tool {tc['name']}: {len(result) if isinstance(result, list) else 1} results")

        if tool_result_blocks:
            state["messages"].append({
                "role": "user",
                "content": tool_result_blocks,
            })

        return state

    def _execute_tool(self, tool_name: str, tool_input: dict) -> list[dict] | dict:
        """Route tool call to the appropriate retrieval method."""
        try:
            if tool_name == "semantic_search":
                return meeting_knowledge_service.semantic_search(
                    query=tool_input["query"],
                    top_k=tool_input.get("top_k", settings.FATHOM_TOP_K),
                )
            elif tool_name == "filter_by_category":
                return meeting_knowledge_service.filter_by_category(
                    category=tool_input["category"],
                    query=tool_input["query"],
                    top_k=tool_input.get("top_k", settings.FATHOM_TOP_K),
                )
            elif tool_name == "search_by_section_type":
                return meeting_knowledge_service.search_by_section_type(
                    section_type=tool_input["section_type"],
                    query=tool_input["query"],
                    top_k=tool_input.get("top_k", settings.FATHOM_TOP_K),
                )
            elif tool_name == "filter_by_customer":
                return meeting_knowledge_service.filter_by_customer(
                    customer_name=tool_input["customer_name"],
                    top_k=tool_input.get("top_k", settings.FATHOM_TOP_K),
                )
            elif tool_name == "get_meeting_details":
                return meeting_knowledge_service.get_meeting_details(
                    meeting_id=tool_input["meeting_id"],
                )
            elif tool_name == "search_fathom_api":
                return self._search_fathom_live(
                    query=tool_input["query"],
                    days_back=tool_input.get("days_back", 30),
                )
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Tool execution failed ({tool_name}): {e}")
            return {"error": str(e)}

    def _search_fathom_live(self, query: str, days_back: int = 30) -> list[dict]:
        """
        Fallback: search the live Fathom API for recent meetings matching the query.
        Returns results in the same format as knowledge base tools.
        """
        import asyncio
        from datetime import timedelta

        if not settings.FATHOM_API_KEY:
            return [{"error": "Fathom API key not configured"}]

        async def _fetch():
            from app.services.fathom_service import fathom_service, FathomAPIError

            since = datetime.now(timezone.utc) - timedelta(days=days_back)
            created_after = since.strftime("%Y-%m-%dT%H:%M:%SZ")

            try:
                meetings = await fathom_service.list_all_meetings(
                    created_after=created_after,
                    include_summary=True,
                    include_action_items=True,
                )
            except FathomAPIError as e:
                logger.error(f"Fathom API search failed: {e}")
                return [{"error": f"Fathom API error: {e}"}]

            # Filter meetings by keyword match in title or summary
            query_lower = query.lower()
            query_words = set(query_lower.split())
            results = []
            for meeting in meetings:
                title = (meeting.get("title") or "").lower()
                summary_data = meeting.get("default_summary") or {}
                summary_text = (summary_data.get("markdown_formatted") or "").lower()
                action_items = meeting.get("action_items") or []

                # Score by keyword overlap
                search_text = f"{title} {summary_text}"
                score = sum(1 for w in query_words if w in search_text)
                if score == 0:
                    continue

                # Format to match knowledge base result shape
                results.append({
                    "meeting_id": str(meeting.get("recording_id", "")),
                    "meeting_title": meeting.get("title", ""),
                    "category": "Live API Result",
                    "section_type": "key_takeaways",
                    "text": (summary_data.get("markdown_formatted") or "")[:1000],
                    "similarity": round(score / max(len(query_words), 1), 4),
                    "source": "fathom_api",
                })

            # Sort by relevance and limit
            results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            return results[:5]

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_fetch())
        except Exception as e:
            logger.error(f"Live Fathom API search failed: {e}")
            return [{"error": str(e)}]
        finally:
            loop.close()

    def _force_synthesis(self, state: FathomState) -> FathomState:
        """Force a final answer after max tool calls exhausted."""
        from app.services import claude_service

        # Build a synthesis prompt from all tool results
        context_parts = []
        for tr in state["tool_results"]:
            results = tr["result"]
            if isinstance(results, list):
                for chunk in results[:3]:
                    text = chunk.get("text", "")[:500]
                    if text:
                        context_parts.append(f"[{chunk.get('category', '')} / {chunk.get('section_type', '')}] {text}")

        synthesis_prompt = f"""Based on the following retrieved information, answer the user's question.

Question: {state['query']}

Retrieved Context:
{chr(10).join(context_parts[:15])}

Provide a clear, concise answer. Anonymize any customer names."""

        try:
            response = claude_service.call_claude(
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": synthesis_prompt}],
                max_tokens=2048,
                temperature=0.3,
            )
            if response and response.content:
                text_parts = [b.text for b in response.content if b.type == "text"]
                state["final_answer"] = "\n".join(text_parts).strip()
            else:
                state["final_answer"] = "I found some relevant information but was unable to synthesize a complete answer."
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            state["final_answer"] = "I retrieved relevant meeting records but encountered an error during synthesis."

        return state

    def _build_messages(self, state: FathomState) -> list[dict]:
        """Build the message list for Claude, including conversation history."""
        messages = []

        # Include recent conversation history for context
        for msg in state["conversation_history"][-5:]:
            messages.append(msg)

        # Add the current query if no tool calls yet
        if not state["messages"]:
            messages.append({
                "role": "user",
                "content": state["query"],
            })
        else:
            # First message was the query
            if not any(m.get("role") == "user" and isinstance(m.get("content"), str) for m in messages):
                messages.append({
                    "role": "user",
                    "content": state["query"],
                })
            messages.extend(state["messages"])

        return messages

    def _extract_sources(self, tool_results: list[dict]) -> list[dict]:
        """Extract unique source references from tool results."""
        seen = set()
        sources = []
        for tr in tool_results:
            results = tr["result"]
            if isinstance(results, list):
                for chunk in results:
                    mid = chunk.get("meeting_id", "")
                    if mid and mid not in seen:
                        seen.add(mid)
                        sources.append({
                            "meeting_id": mid,
                            "meeting_title": chunk.get("meeting_title", ""),
                            "category": chunk.get("category", ""),
                        })
        return sources
