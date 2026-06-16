"""
Centralised API client.
Every HTTP call to the FastAPI backend lives here — never scattered
across pages. If the API URL changes, you change it in one place.
"""
import requests
import streamlit as st
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# At the top of api_client.py — find the API_BASE line and replace with:
import os
API_BASE = os.getenv(
    "API_BASE_URL",
    "https://credit-risk-api-i7bq.onrender.com"   # fallback to Render
)
TIMEOUT  = 30  # seconds


def _headers() -> dict:
    """Injects the JWT token from session state into every request."""
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _handle(response: requests.Response) -> dict:
    """Unified response handler — raises clean errors on failure."""
    if response.status_code == 401:
        st.session_state.clear()
        st.error("Session expired. Please log in again.")
        st.rerun()
    if not response.ok:
        detail = response.json().get("detail", "Unknown error")
        raise RuntimeError(f"API error {response.status_code}: {detail}")
    return response.json()


# ── Auth ──────────────────────────────────────
def register(username: str, email: str, password: str) -> dict:
    r = requests.post(f"{API_BASE}/auth/register", json={
        "username": username, "email": email, "password": password
    }, timeout=TIMEOUT)
    return _handle(r)


def login(username: str, password: str) -> str:
    """Returns access token string."""
    r = requests.post(f"{API_BASE}/auth/login", json={
        "username": username, "password": password
    }, timeout=TIMEOUT)
    data = _handle(r)
    return data["access_token"]


# ── Predictions ───────────────────────────────
def predict(payload: dict) -> dict:
    r = requests.post(
        f"{API_BASE}/predict",
        json=payload,
        headers=_headers(),
        timeout=TIMEOUT,
    )
    return _handle(r)


def explain(prediction_id: str) -> dict:
    r = requests.post(
        f"{API_BASE}/explain/{prediction_id}",
        headers=_headers(),
        timeout=TIMEOUT,
    )
    return _handle(r)


# ── History ───────────────────────────────────
def get_history(page: int = 1, per_page: int = 20, decision: str = None) -> dict:
    params = {"page": page, "per_page": per_page}
    if decision:
        params["decision"] = decision
    r = requests.get(
        f"{API_BASE}/history",
        params=params,
        headers=_headers(),
        timeout=TIMEOUT,
    )
    return _handle(r)


def get_prediction_detail(prediction_id: str) -> dict:
    r = requests.get(
        f"{API_BASE}/history/{prediction_id}",
        headers=_headers(),
        timeout=TIMEOUT,
    )
    return _handle(r)


# ── Health ────────────────────────────────────
def health_check() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.ok
    except Exception:
        return False
    
def get_counsel(prediction_id: str) -> dict:
    """Get AI credit improvement advice for a prediction."""
    r = requests.post(
        f"{API_BASE}/counsel/{prediction_id}",
        headers=_headers(),
        timeout=35,   # Claude can take up to 30s
    )
    return _handle(r)