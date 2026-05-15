import streamlit as st
from datetime import datetime
from config import (
    page_setup, require_auth, page_title, divider,
    stat_card, status_badge, trust_badge, trust_ring_svg,
    fmt, trust_color,
    GOLD, BG_SURFACE, BG_RAISED, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    SUCCESS, WARNING,
)
import api

page_setup("NitaRefund · Dashboard")
require_auth()

username = st.session_state.get("username", "User")


# ── Load all data ─────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def load_dashboard(token):
    try:    summary = api.get_summary()
    except: summary = {"total_lent": 0, "total_borrowed": 0, "pending_count": 0, "total_count": 0}

    try:    txns    = api.get_my_transactions(limit=10)
    except: txns    = []

    try:    network = api.get_my_network()
    except: network = []

    try:    balance = api.get_wallet_balance()
    except: balance = 0.0

    return summary, txns, network, balance

summary, txns, network, balance = load_dashboard(st.session_state.token)

is_new = summary["total_count"] == 0


# ── Header row ────────────────────────────────────────────────
h_left, h_right = st.columns([8, 2])

with h_left:
    greeting = "Welcome to NitaRefund" if is_new else f"Welcome back, {username}"
    subtitle = (
        "Let's get you set up — create your first transaction below."
        if is_new else
        "Here's a summary of your peer lending activity."
    )
    page_title(greeting, subtitle)

with h_right:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("＋ New Transaction", key="btn_new_tx"):
        st.session_state.show_new_tx = not st.session_state.get("show_new_tx", False)
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
    if st.button("Log out", key="btn_logout"):
        st.session_state.clear()
        st.switch_page("app.py")
    st.markdown('</div>', unsafe_allow_html=True)

divider()


# ── Stat cards ────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1: stat_card("Wallet Balance",     fmt(balance), accent=True)
with c2: stat_card("Total Lent Out",     fmt(summary["total_lent"]))
with c3: stat_card("Total Borrowed",     fmt(summary["total_borrowed"]))
with c4: stat_card("Pending",            str(summary["pending_count"]) + " txns",
                   sub="awaiting action")
with c5: stat_card("Total Transactions", str(summary["total_count"]))

divider()


# ── User ID card ──────────────────────────────────────────────
user_id_hint = None
if txns:
    for tx in txns:
        if tx.get("lender_username") == username:
            user_id_hint = tx["lender_id"]
            break
        elif tx.get("borrower_username") == username:
            user_id_hint = tx["borrower_id"]
            break

if user_id_hint:
    st.markdown(f"""
    <div style="background:rgba(233,196,106,0.06);border:1px solid rgba(233,196,106,0.20);
                border-radius:12px;padding:14px 20px;margin-bottom:1rem;
                display:flex;align-items:center;gap:16px;">
      <div style="font-size:20px;">🪪</div>
      <div>
        <div style="font-size:11px;color:{TEXT_MUTED};text-transform:uppercase;
                    letter-spacing:0.06em;margin-bottom:3px;">Your User ID</div>
        <div style="font-size:28px;font-family:'DM Serif Display',Georgia,serif;
                    color:{GOLD};letter-spacing:-0.01em;">{user_id_hint}</div>
        <div style="font-size:12px;color:{TEXT_MUTED};margin-top:2px;">
          Share this with peers so they can include you in transactions
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── New Transaction form (inline, toggled) ────────────────────
if st.session_state.get("show_new_tx"):
    st.markdown(f"""
    <div style="font-family:'DM Serif Display',Georgia,serif;font-size:20px;
                color:{TEXT_PRIMARY};margin-bottom:4px;">New Transaction</div>
    <p style="font-size:13px;color:{TEXT_MUTED};margin-bottom:1rem;">
      You are the lender. Enter the borrower's User ID.
    </p>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        borrower_id = st.number_input("Borrower User ID", min_value=1, step=1,
                                      key="tx_borrower")
        amount = st.number_input("Amount (KES)", min_value=1.0, step=100.0,
                                 key="tx_amount")
    with col_b:
        tx_type  = st.selectbox("Type", ["monetary", "service"], key="tx_type")
        due_date = st.date_input("Due Date (optional)", value=None, key="tx_due")

    description = st.text_input("Description (optional)", key="tx_desc",
                                placeholder="e.g. lunch money, rent split")

    btn_l, btn_r = st.columns([3, 1])
    with btn_l:
        if st.button("Create Transaction", key="btn_create_tx"):
            try:
                api.create_transaction(
                    borrower_id=int(borrower_id),
                    amount=float(amount),
                    tx_type=tx_type,
                    description=description,
                    due_date=due_date if due_date else None,
                )
                st.success("Transaction created. The borrower needs to approve it.")
                st.session_state.show_new_tx = False
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                msg = getattr(getattr(e, "response", None), "json", lambda: {})()
                st.error(msg.get("detail", "Could not create transaction."))
    with btn_r:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("Cancel", key="btn_cancel_tx"):
            st.session_state.show_new_tx = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    divider()


# ── Main two-column layout ────────────────────────────────────
left_col, right_col = st.columns([6, 4], gap="large")


# ═════════════════════════════════════════════════════════════
# LEFT — Recent Transactions
# ═════════════════════════════════════════════════════════════
with left_col:
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;
                align-items:baseline;margin-bottom:1rem;">
      <div style="font-family:'DM Serif Display',Georgia,serif;
                  font-size:20px;color:{TEXT_PRIMARY};">
        Recent Transactions
      </div>
      <div style="font-size:12px;color:{TEXT_MUTED};">Last 10</div>
    </div>
    """, unsafe_allow_html=True)

    if not txns:
        st.markdown(f"""
        <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                    border-radius:14px;padding:3rem 2rem;text-align:center;">
          <div style="font-size:36px;margin-bottom:12px;">📋</div>
          <div style="font-size:15px;font-weight:500;
                      color:{TEXT_PRIMARY};margin-bottom:6px;">
            No transactions yet
          </div>
          <div style="font-size:13px;color:{TEXT_MUTED};">
            Create your first transaction using the button above.<br>
            You'll need your peer's User ID.
          </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # Open container
        st.markdown(
            f'<div style="background:{BG_SURFACE};border:1px solid {BORDER};'
            f'border-radius:14px;overflow:hidden;">',
            unsafe_allow_html=True
        )

        for i, tx in enumerate(txns):
            is_lender    = tx["lender_username"] == username
            counterparty = tx["borrower_username"] if is_lender else tx["lender_username"]
            direction    = "Lent to" if is_lender else "Borrowed from"
            dir_color    = SUCCESS if is_lender else WARNING
            amount_sign  = f"+{fmt(tx['amount'])}" if is_lender else f"−{fmt(tx['amount'])}"
            border       = f"border-bottom:1px solid {BORDER};" if i < len(txns) - 1 else ""
            arrow        = "↑" if is_lender else "↓"

            try:
                dt       = datetime.fromisoformat(tx["created_at"].replace("Z", "+00:00"))
                time_str = dt.strftime("%-d %b %Y, %I:%M %p")
            except Exception:
                time_str = str(tx.get("created_at", ""))[:10]

            desc_html = (
                f'<div style="font-size:11px;color:{TEXT_MUTED};margin-top:2px;">'
                f'{tx["description"]}</div>'
            ) if tx.get("description") else ""

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;
                        padding:14px 18px;{border}">
              <div style="width:36px;height:36px;border-radius:50%;flex-shrink:0;
                          background:{BG_RAISED};display:flex;align-items:center;
                          justify-content:center;font-size:15px;color:{dir_color};">
                {arrow}
              </div>
              <div style="flex:1;min-width:0;">
                <div style="font-size:13px;font-weight:500;color:{TEXT_PRIMARY};">
                  {direction} <span style="color:{GOLD};">{counterparty}</span>
                </div>
                <div style="font-size:11px;color:{TEXT_MUTED};margin-top:2px;">
                  {time_str}
                </div>
                {desc_html}
              </div>
              <div style="text-align:right;flex-shrink:0;">
                <div style="font-size:14px;font-weight:500;color:{dir_color};
                            font-family:'DM Serif Display',Georgia,serif;">
                  {amount_sign}
                </div>
                <div style="margin-top:4px;">
                  {status_badge(tx["status"])}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # Close container
        st.markdown('</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
# RIGHT — Trust Score + Network
# ═════════════════════════════════════════════════════════════
with right_col:

    # Trust ring
    avg_score = (
        sum(p["score"] for p in network) / len(network)
        if network else 50.0
    )

    st.markdown(f"""
    <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                border-radius:14px;padding:20px 24px;margin-bottom:1rem;">
      <div style="font-family:'DM Serif Display',Georgia,serif;
                  font-size:18px;color:{TEXT_PRIMARY};margin-bottom:16px;">
        Your Trust Score
      </div>
      <div style="display:flex;justify-content:center;">
        {trust_ring_svg(avg_score, size=130)}
      </div>
      <div style="font-size:12px;color:{TEXT_MUTED};
                  text-align:center;margin-top:14px;">
        Average across {len(network)} peer{"s" if len(network) != 1 else ""}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Trust network header
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;
                align-items:baseline;margin-bottom:10px;">
      <div style="font-family:'DM Serif Display',Georgia,serif;
                  font-size:18px;color:{TEXT_PRIMARY};">
        Trust Network
      </div>
      <div style="font-size:12px;color:{TEXT_MUTED};">Top 10</div>
    </div>
    """, unsafe_allow_html=True)

    if not network:
        st.markdown(f"""
        <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                    border-radius:14px;padding:2rem;text-align:center;">
          <div style="font-size:28px;margin-bottom:8px;">🤝</div>
          <div style="font-size:14px;color:{TEXT_MUTED};">
            No peers yet.<br>
            Complete a transaction to build your network.
          </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # Open container
        st.markdown(
            f'<div style="background:{BG_SURFACE};border:1px solid {BORDER};'
            f'border-radius:14px;overflow:hidden;">',
            unsafe_allow_html=True
        )

        for i, peer in enumerate(network[:10]):
            score  = float(peer["score"])
            color  = trust_color(score)
            border = f"border-bottom:1px solid {BORDER};" if i < min(len(network), 10) - 1 else ""
            initial = peer["username"][0].upper()

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;
                        padding:12px 16px;{border}">
              <div style="width:32px;height:32px;border-radius:50%;
                          background:{BG_RAISED};flex-shrink:0;
                          display:flex;align-items:center;justify-content:center;
                          font-size:12px;color:{TEXT_MUTED};font-weight:600;">
                {initial}
              </div>
              <div style="flex:1;font-size:13px;font-weight:500;color:{TEXT_PRIMARY};">
                {peer["username"]}
              </div>
              <div style="font-family:'DM Serif Display',Georgia,serif;
                          font-size:18px;color:{color};line-height:1;margin-right:8px;">
                {round(score)}
              </div>
              <div>{trust_badge(score)}</div>
            </div>
            """, unsafe_allow_html=True)

        # Close container
        st.markdown('</div>', unsafe_allow_html=True)