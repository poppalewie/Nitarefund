import requests
import streamlit as st
from config import API_URL


def _headers():
    """Returns auth header if a token exists in session."""
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def get(path: str, **kwargs):
    return requests.get(f"{API_URL}{path}", headers=_headers(), **kwargs)


def post(path: str, json=None, data=None, **kwargs):
    return requests.post(
        f"{API_URL}{path}",
        headers=_headers(),
        json=json,
        data=data,
        **kwargs,
    )


# ── Auth ──────────────────────────────────────────────────────

def login(username: str, password: str) -> dict:
    # FastAPI's OAuth2 expects form data, not JSON
    r = requests.post(
        f"{API_URL}/auth/login",
        data={"username": username, "password": password},
    )
    r.raise_for_status()
    return r.json()


def register(username: str, email: str, password: str, security_answer: str) -> dict:
    r = requests.post(
        f"{API_URL}/auth/register",
        json={"username": username, "email": email,
              "password": password, "security_answer": security_answer},
    )
    r.raise_for_status()
    return r.json()


def reset_password(email: str, security_answer: str, new_password: str) -> dict:
    r = requests.post(
        f"{API_URL}/auth/reset-password",
        json={"email": email, "security_answer": security_answer,
              "new_password": new_password},
    )
    r.raise_for_status()
    return r.json()


# ── Leaderboard (no auth needed) ─────────────────────────────

def get_leaderboard() -> list:
    try:
        r = requests.get(f"{API_URL}/trust/leaderboard", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


# ── Transactions ──────────────────────────────────────────────

def create_transaction(borrower_id, amount, tx_type="monetary",
                       description="", due_date=None) -> dict:
    payload = {"borrower_id": borrower_id, "amount": amount,
               "transaction_type": tx_type}
    if description: payload["description"] = description
    if due_date:    payload["due_date"] = str(due_date)
    r = post("/transactions/", json=payload)
    r.raise_for_status()
    return r.json()


def transaction_action(tx_id: int, action: str) -> dict:
    # action: approve, pay, confirm, cancel, dispute, reject
    r = post(f"/transactions/{tx_id}/{action}")
    r.raise_for_status()
    return r.json()


# ── Trust ─────────────────────────────────────────────────────

def get_my_network() -> list:
    r = get("/trust/me/network")
    r.raise_for_status()
    return r.json()


# ADD THIS BELOW ↓
def get_pair_trust(user_id: int) -> dict:
    r = get(f"/trust/pair/{user_id}")
    r.raise_for_status()
    return r.json()


def get_trust_history() -> list:
    r = get("/trust/me/history")
    r.raise_for_status()
    return r.json()


# ── Groups ────────────────────────────────────────────────────

def create_group(user_ids: list, total_amount: float, description="") -> dict:
    r = post("/groups/", json={"user_ids": user_ids,
                                "total_amount": total_amount,
                                "description": description})
    r.raise_for_status()
    return r.json()

def get_my_transactions(limit=10) -> list:
    r = get(f"/transactions/?limit={limit}")
    r.raise_for_status()
    return r.json()


def get_summary() -> dict:
    r = get("/transactions/summary")
    r.raise_for_status()
    return r.json()


def get_wallet_balance() -> float:
    r = get("/wallet/balance")
    r.raise_for_status()
    return r.json().get("balance", 0.0)


def list_users() -> list:
    r = get("/users/")
    r.raise_for_status()
    return r.json()

def get_trust_history() -> list:
    r = get("/trust/me/history")
    r.raise_for_status()
    return r.json()

def get_my_groups() -> list:
    r = get("/groups/")
    r.raise_for_status()
    return r.json()

def get_me() -> dict:
    r = get("/auth/me")
    r.raise_for_status()
    return r.json()

def get_wallet_leaderboard() -> list:
    r = get("/wallet/leaderboard")
    r.raise_for_status()
    return r.json()


def get_spending_categories() -> list:
    r = get("/wallet/categories")
    r.raise_for_status()
    return r.json()