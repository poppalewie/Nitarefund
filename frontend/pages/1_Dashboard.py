import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from config import (
    page_setup, require_auth, page_title, divider, sidebar_nav,
    stat_card, status_badge, trust_badge, trust_ring_svg,
    fmt, trust_color, PLOTLY_LAYOUT,
    GOLD, BG_SURFACE, BG_RAISED, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    SUCCESS, WARNING,
)
import api

page_setup("NitaRefund · Dashboard")
require_auth()
sidebar_nav("Dashboard")

username = st.session_state.get("username", "User")


@st.cache_data(ttl=30, show_spinner=False)
def load_dashboard(token):
    try:    summary = api.get_summary()
    except: summary = {"total_lent": 0, "total_borrowed": 0,
                       "pending_count": 0, "total_count": 0}
    try:    txns    = api.get_my_transactions(limit=10)
    except: txns    = []
    try:    network = api.get_my_network()
    except: network = []
    try:    balance = api.get_wallet_balance()
    except: balance = 0.0
    try:    me      = api.get_me()
    except: me      = {}
    return summary, txns, network, balance, me

summary, txns, network, balance, me = load_dashboard(st.session_state.token)
is_new  = summary["total_count"] == 0
user_id = me.get("id")

# ── Header ────────────────────────────────────────────────────
greeting = "Welcome to NitaRefund" if is_new else f"Welcome back, {username}"
subtitle = (
    "Let's get you set up — create your first transaction below."
    if is_new else
    "Here's a summary of your peer lending activity."
)
page_title(greeting, subtitle)
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
if user_id:
    st.markdown(f"""
    <div style="background:rgba(233,196,106,0.06);border:1px solid rgba(233,196,106,0.20);
                border-radius:12px;padding:14px 20px;margin-bottom:1.5rem;
                display:flex;align-items:center;gap:16px;">
      <div style="font-size:20px;">🪪</div>
      <div>
        <div style="font-size:11px;color:{TEXT_MUTED};text-transform:uppercase;
                    letter-spacing:0.06em;margin-bottom:3px;">Your User ID</div>
        <div style="font-size:28px;font-family:'DM Serif Display',Georgia,serif;
                    color:{GOLD};">{user_id}</div>
        <div style="font-size:12px;color:{TEXT_MUTED};margin-top:2px;">
          Share this with peers so they can include you in transactions
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── Main layout ───────────────────────────────────────────────
left_col, right_col = st.columns([6, 4], gap="large")

# ═══════════════════════════════════════════════════
# LEFT — Transactions + Lent vs Borrowed chart
# ═══════════════════════════════════════════════════
with left_col:

    # ── Lent vs Borrowed per peer chart ──────────────
    if txns:
        peer_lent     = {}
        peer_borrowed = {}

        for tx in txns:
            is_lender    = tx["lender_username"] == username
            counterparty = tx["borrower_username"] if is_lender else tx["lender_username"]
            amount       = float(tx["amount"])
            if tx["status"] in ("settled", "auto_settled"):
                if is_lender:
                    peer_lent[counterparty]     = peer_lent.get(counterparty, 0) + amount
                else:
                    peer_borrowed[counterparty] = peer_borrowed.get(counterparty, 0) + amount

        peers = sorted(set(list(peer_lent.keys()) + list(peer_borrowed.keys())))

        if peers:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Lent",
                x=peers,
                y=[peer_lent.get(p, 0) for p in peers],
                marker_color=SUCCESS,
                marker_opacity=0.8,
            ))
            fig.add_trace(go.Bar(
                name="Borrowed",
                x=peers,
                y=[peer_borrowed.get(p, 0) for p in peers],
                marker_color=WARNING,
                marker_opacity=0.8,
            ))
            layout = dict(PLOTLY_LAYOUT)
            layout.update(
                title="Lent vs Borrowed per Peer (settled)",
                barmode="group",
                legend=dict(orientation="h", y=1.1),
                height=260,
            )
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True)

    # ── Recent transactions header ────────────────────
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
                      color:{TEXT_PRIMARY};margin-bottom:6px;">No transactions yet</div>
          <div style="font-size:13px;color:{TEXT_MUTED};">
            Use ＋ New Transaction in the sidebar to get started.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
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
                {"↑" if is_lender else "↓"}
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
                <div style="margin-top:4px;">{status_badge(tx["status"])}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# RIGHT — Trust score + network
# ═══════════════════════════════════════════════════
with right_col:
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
      <div style="font-size:12px;color:{TEXT_MUTED};text-align:center;margin-top:14px;">
        Average across {len(network)} peer{"s" if len(network) != 1 else ""}
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;
                align-items:baseline;margin-bottom:10px;">
      <div style="font-family:'DM Serif Display',Georgia,serif;
                  font-size:18px;color:{TEXT_PRIMARY};">Trust Network</div>
      <div style="font-size:12px;color:{TEXT_MUTED};">Top 10</div>
    </div>
    """, unsafe_allow_html=True)

    if not network:
        st.markdown(f"""
        <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                    border-radius:14px;padding:2rem;text-align:center;">
          <div style="font-size:28px;margin-bottom:8px;">🤝</div>
          <div style="font-size:14px;color:{TEXT_MUTED};">
            No peers yet.<br>Complete a transaction to build your network.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="background:{BG_SURFACE};border:1px solid {BORDER};'
            f'border-radius:14px;overflow:hidden;">',
            unsafe_allow_html=True
        )
        for i, peer in enumerate(network[:10]):
            score   = float(peer["score"])
            color   = trust_color(score)
            border  = f"border-bottom:1px solid {BORDER};" if i < min(len(network), 10) - 1 else ""
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
        st.markdown('</div>', unsafe_allow_html=True)