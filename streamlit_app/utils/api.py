"""
API client for the CS Control Plane FastAPI backend.
"""

import os
import time
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
_token = None


def _headers():
    return {"Authorization": f"Bearer {_token}"} if _token else {}


def login(email: str, password: str) -> dict:
    """Login and store the token."""
    global _token
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    resp.raise_for_status()
    data = resp.json()
    _token = data.get("access_token")
    return data


def get(path: str, params: dict | None = None) -> dict:
    """GET request to the backend API."""
    resp = requests.get(f"{BASE_URL}{path}", headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def post(path: str, json_data: dict | None = None) -> dict:
    """POST request to the backend API."""
    resp = requests.post(f"{BASE_URL}{path}", headers=_headers(), json=json_data, timeout=120)
    resp.raise_for_status()
    return resp.json()


def delete(path: str) -> dict:
    """DELETE request to the backend API."""
    resp = requests.delete(f"{BASE_URL}{path}", headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── Convenience methods ──

def get_customers(limit: int = 50) -> list:
    data = get("/customers", {"limit": limit})
    return data.get("customers", data) if isinstance(data, dict) else data


def get_customer(customer_id: str) -> dict:
    return get(f"/customers/{customer_id}")


def get_dashboard_stats() -> dict:
    return get("/dashboard/stats")


def get_tickets(limit: int = 50, severity: str = "", status: str = "") -> list:
    params = {"limit": limit}
    if severity:
        params["severity"] = severity
    if status:
        params["status"] = status
    data = get("/tickets", params)
    return data.get("tickets", data) if isinstance(data, dict) else data


def get_agents() -> list:
    """Get agent hierarchy from v2 endpoint, fallback to v1."""
    try:
        data = get("/v2/hierarchy/agents")
        return data.get("agents", data) if isinstance(data, dict) else data
    except Exception:
        data = get("/agents")
        return data.get("agents", data) if isinstance(data, dict) else data


def get_health_scores(customer_id: str, days: int = 30) -> list:
    data = get(f"/customers/{customer_id}/health", {"days": days})
    return data.get("scores", data) if isinstance(data, dict) else data


def get_call_insights(limit: int = 20) -> list:
    data = get("/insights", {"limit": limit})
    return data.get("insights", data) if isinstance(data, dict) else data


def get_alerts(limit: int = 20) -> list:
    data = get("/alerts", {"limit": limit})
    return data.get("alerts", data) if isinstance(data, dict) else data


def get_recent_events(limit: int = 20) -> list:
    data = get("/events", {"limit": limit})
    return data.get("events", data) if isinstance(data, dict) else data


# ── Executive Summary ──

def get_executive_summary(days: int = 30) -> dict:
    return get("/executive/summary", {"days": days})


def get_executive_trends(days: int = 30) -> dict:
    return get("/executive/trends", {"days": days})


def run_alert_rules() -> dict:
    return post("/executive/check-rules")


# ── Chat ──

def send_chat_message(text: str, customer_id: str | None = None, conversation_id: str | None = None) -> dict:
    """Send a chat message. Returns immediately with message_id (processing is async)."""
    payload = {"message": text}
    if customer_id:
        payload["customer_id"] = customer_id
    if conversation_id:
        payload["conversation_id"] = conversation_id
    return post("/chat/send", payload)


def get_conversations(limit: int = 20) -> list:
    data = get("/chat/conversations", {"limit": limit})
    return data.get("conversations", data) if isinstance(data, dict) else data


def get_conversation(conversation_id: str) -> dict:
    return get(f"/chat/conversations/{conversation_id}")


def poll_for_response(conversation_id: str, message_id: str, timeout: int = 360) -> dict | None:
    """Poll for the assistant's response to complete.

    Looks for the latest assistant message in the conversation that has
    a completed or failed pipeline_status.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            conv = get_conversation(str(conversation_id))
            messages = conv.get("messages", [])
            # Find the latest assistant message
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    pipeline_status = msg.get("pipeline_status", "")
                    if pipeline_status in ("completed", "failed"):
                        return msg
                    break  # Found assistant msg but still processing
            time.sleep(3)
        except Exception:
            time.sleep(5)
    return None
