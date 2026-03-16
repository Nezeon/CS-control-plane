"""
Ask AI — Chat interface for querying the CS Control Plane.
This is the primary interface for interacting with the 13-agent hierarchy.
"""

import streamlit as st
import time
from utils.style import inject_css
from utils import api

st.set_page_config(page_title="Ask AI | CS Control Plane", page_icon="💬", layout="wide")
inject_css()

if not st.session_state.get("authenticated"):
    st.warning("Please sign in first.")
    st.page_link("app.py", label="Go to Login")
    st.stop()

# ── Session State ──
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "processing" not in st.session_state:
    st.session_state.processing = False

# ── Header ──
st.markdown("# 💬 Ask AI")
st.markdown("Query the CS Control Plane. Your question is routed through the 4-tier agent hierarchy.")

# ── Sidebar: Conversation Controls ──
with st.sidebar:
    st.markdown("### Conversations")
    if st.button("New Conversation", use_container_width=True):
        st.session_state.chat_messages = []
        st.session_state.conversation_id = None
        st.rerun()

    st.divider()
    st.markdown("**Suggested queries:**")
    suggestions = [
        "Which customer is at highest risk of churn?",
        "What are the top issues across all customers?",
        "Summarize recent QBR calls",
        "What happened in the last Fathom recording?",
        "Show me P1 tickets and their status",
        "What features are customers requesting most?",
    ]
    for suggestion in suggestions:
        if st.button(suggestion, key=f"sug_{hash(suggestion)}", use_container_width=True):
            st.session_state.pending_query = suggestion
            st.rerun()

# ── Chat History ──
for msg in st.session_state.chat_messages:
    role = msg["role"]
    with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "🤖"):
        st.markdown(msg["content"])
        if role == "assistant" and msg.get("agents"):
            agents_str = ", ".join(msg["agents"])
            st.caption(f"Agents: {agents_str}")

# ── Handle pending query from sidebar suggestion ──
pending = st.session_state.pop("pending_query", None)

# ── Chat Input ──
user_input = st.chat_input("Ask about customers, tickets, calls, health scores...")

query = pending or user_input

if query and not st.session_state.processing:
    st.session_state.processing = True

    # Add user message
    st.session_state.chat_messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(query)

    # Send to backend
    with st.chat_message("assistant", avatar="🤖"):
        with st.status("Processing your query...", expanded=True) as status:
            try:
                st.write("Sending to orchestrator...")
                result = api.send_chat_message(
                    text=query,
                    conversation_id=st.session_state.conversation_id,
                )

                conversation_id = result.get("conversation_id")
                message_id = result.get("message_id") or result.get("assistant_message_id")
                st.session_state.conversation_id = conversation_id

                st.write("Orchestrator routing to agents...")
                st.write("Agent pipeline running (this may take 2-5 minutes)...")

                # Poll for response — pipeline runs T1→T2→T3 with multiple Claude calls
                response = api.poll_for_response(conversation_id, message_id, timeout=360)

                if response:
                    content = response.get("content", "No response received.")
                    agents = response.get("agents_involved", [])
                    pipeline_status = response.get("pipeline_status", "unknown")

                    if pipeline_status == "failed":
                        status.update(label="Pipeline failed", state="error")
                        st.error(content)
                    else:
                        status.update(label="Complete", state="complete")
                        st.markdown(content)
                        if agents:
                            st.caption(f"Agents involved: {', '.join(agents)}")

                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": content,
                        "agents": agents,
                    })
                else:
                    status.update(label="Timeout", state="error")
                    timeout_msg = "Response timed out. The agents may still be processing — try again in a moment."
                    st.warning(timeout_msg)
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": timeout_msg,
                        "agents": [],
                    })

            except Exception as e:
                status.update(label="Error", state="error")
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "agents": [],
                })

    st.session_state.processing = False
