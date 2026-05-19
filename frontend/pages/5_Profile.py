import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from config import (
    page_setup, require_auth, page_title, divider, sidebar_nav,
    stat_card, trust_ring_svg, fmt, trust_color, PLOTLY_LAYOUT,
    GOLD, BG_SURFACE, BG_RAISED, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    SUCCESS, DANGER, WARNING, INFO,
)
import api

page_setup("NitaRefund · Profile")
require_auth()
sidebar_nav("Profile")

username = st.session_state.get("username", "User")


@st.cache_data(ttl=30, show_spinner=False)
def load_profile(token):
    try:    summary = api.get_summary()
    except: summary = {"total_lent": 0, "total_borrowed": 0,
                       "pending_count": 0, "total_count": 0}
    try:    network = api.get_my_network()
    except: network = []
    try:    balance = api.get_wallet_balance()
    except: balance = 0.0
    try:    txns    = api.get_my_transactions(limit=50)
    except: txns    = []
    return summary, network, balance, txns

summary, network, balance, txns = load_profile(st.session_state.token)

avg_score = (
    sum(p["score"] for p in network) / len(network)
    if network else 50.0
)

page_title(username, "Your account overview and activity analytics.")
divider()

# ── Row 1: account card + trust ring ─────────────────────────
info_col, ring_col = st.columns([6, 3], gap="large")

with info_col:
    # Get user ID from transactions
    user_id_hint = None
    for tx in txns:
        if tx.get("lender_username") == username:
            user_id_hint = tx["lender_id"]; break
        elif tx.get("borrower_username") == username:
            user_id_hint = tx["borrower_id"]; break

    # Account card — open container
    st.markdown(f"""
    <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                border-radius:14px;padding:20px 24px;margin-bottom:1rem;">
    <div style="font-size:11px;color:{TEXT_MUTED};text-transform:uppercase;
                letter-spacing:0.06em;margin-bottom:12px;">Account</div>
    """, unsafe_allow_html=True)

    # Each row rendered separately so special chars can't break the block
    def account_row(label, value, value_color=None, last=False):
        color = value_color or TEXT_PRIMARY
        border = "" if last else f"border-bottom:1px solid {BORDER};"
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;
                    align-items:center;padding:10px 0;{border}">
            <span style="font-size:13px;color:{TEXT_SECONDARY};">{label}</span>
            <span style="font-size:13px;font-weight:500;color:{color};">{value}</span>
        </div>
        """, unsafe_allow_html=True)

    account_row("Username",          username)
    account_row("User ID",           str(user_id_hint) if user_id_hint else "—", GOLD)
    account_row("Wallet Balance",    fmt(balance),                    GOLD)
    account_row("Total Transactions",str(summary['total_count']))
    account_row("Total Lent Out",    fmt(summary['total_lent']),      SUCCESS)
    account_row("Total Borrowed",    fmt(summary['total_borrowed']),  WARNING)
    account_row("Peers in Network",  str(len(network)), last=True)

    # Close container
    st.markdown('</div>', unsafe_allow_html=True)

with ring_col:
    st.markdown(f"""
    <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                border-radius:14px;padding:24px;text-align:center;
                margin-bottom:1rem;">
      <div style="font-family:'DM Serif Display',Georgia,serif;
                  font-size:16px;color:{TEXT_PRIMARY};margin-bottom:16px;">
        Trust Score
      </div>
      <div style="display:flex;justify-content:center;">
        {trust_ring_svg(avg_score, size=120)}
      </div>
      <div style="font-size:12px;color:{TEXT_MUTED};margin-top:12px;">
        {len(network)} peer{"s" if len(network) != 1 else ""} in network
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Net position card
    net = summary["total_lent"] - summary["total_borrowed"]
    net_color = SUCCESS if net >= 0 else WARNING
    net_label = "Net Lender" if net >= 0 else "Net Borrower"
    st.markdown(f"""
    <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                border-radius:14px;padding:16px 20px;text-align:center;">
      <div style="font-size:11px;color:{TEXT_MUTED};text-transform:uppercase;
                  letter-spacing:0.06em;margin-bottom:6px;">Net Position</div>
      <div style="font-family:'DM Serif Display',Georgia,serif;
                  font-size:20px;color:{net_color};">
        {fmt(abs(net))}
      </div>
      <div style="font-size:12px;color:{net_color};margin-top:3px;">{net_label}</div>
    </div>
    """, unsafe_allow_html=True)

divider()

# ── Row 2: Status breakdown + Activity timeline ───────────────
chart_l, chart_r = st.columns(2, gap="large")

with chart_l:
    st.markdown(f"""
    <div style="font-family:'DM Serif Display',Georgia,serif;
                font-size:18px;color:{TEXT_PRIMARY};margin-bottom:12px;">
      Transaction Breakdown
    </div>
    """, unsafe_allow_html=True)

    if txns:
        status_counts = {}
        for tx in txns:
            s = tx["status"].replace("_", " ").capitalize()
            status_counts[s] = status_counts.get(s, 0) + 1

        colors = {
            "Pending":                WARNING,
            "Approved":               INFO,
            "Awaiting confirmation":  GOLD,
            "Settled":                SUCCESS,
            "Auto settled":           SUCCESS,
            "Rejected":               DANGER,
            "Cancelled":              "#666",
            "Disputed":               DANGER,
        }

        labels = list(status_counts.keys())
        values = list(status_counts.values())
        clrs   = [colors.get(l, GOLD) for l in labels]

        fig = go.Figure(go.Pie(
            labels=labels, values=values,
            marker_colors=clrs,
            hole=0.55,
            textinfo="label+percent",
            textfont_size=11,
        ))
        layout = dict(PLOTLY_LAYOUT)
        layout.update(height=280, showlegend=False,
                      margin=dict(l=10, r=10, t=10, b=10))
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(
            f'<p style="color:{TEXT_MUTED};font-size:14px;padding:2rem 0;'
            f'text-align:center;">No data yet.</p>',
            unsafe_allow_html=True
        )

with chart_r:
    st.markdown(f"""
    <div style="font-family:'DM Serif Display',Georgia,serif;
                font-size:18px;color:{TEXT_PRIMARY};margin-bottom:12px;">
      Monthly Activity
    </div>
    """, unsafe_allow_html=True)

    if txns:
        monthly = {}
        for tx in txns:
            try:
                dt    = datetime.fromisoformat(tx["created_at"].replace("Z", "+00:00"))
                month = dt.strftime("%b %Y")
                if month not in monthly:
                    monthly[month] = {"lent": 0, "borrowed": 0}
                if tx["lender_username"] == username:
                    monthly[month]["lent"] += float(tx["amount"])
                else:
                    monthly[month]["borrowed"] += float(tx["amount"])
            except Exception:
                pass

        months = list(monthly.keys())
        lent_vals     = [monthly[m]["lent"]     for m in months]
        borrowed_vals = [monthly[m]["borrowed"] for m in months]

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Lent",     x=months, y=lent_vals,
                             marker_color=SUCCESS, marker_opacity=0.8))
        fig.add_trace(go.Bar(name="Borrowed", x=months, y=borrowed_vals,
                             marker_color=WARNING, marker_opacity=0.8))
        layout = dict(PLOTLY_LAYOUT)
        layout.update(height=280, barmode="group",
                      legend=dict(orientation="h", y=1.1),
                      margin=dict(l=10, r=10, t=30, b=20))
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(
            f'<p style="color:{TEXT_MUTED};font-size:14px;padding:2rem 0;'
            f'text-align:center;">No data yet.</p>',
            unsafe_allow_html=True
        )

divider()

# ── Row 3: Peer relationship table ────────────────────────────
st.markdown(f"""
<div style="font-family:'DM Serif Display',Georgia,serif;
            font-size:20px;color:{TEXT_PRIMARY};margin-bottom:4px;">
  Peer Relationships
</div>
<div style="font-size:13px;color:{TEXT_MUTED};margin-bottom:1rem;">
  Total exchanged and net balance with each peer across all settled transactions.
</div>
""", unsafe_allow_html=True)

if not txns:
    st.markdown(
        f'<p style="color:{TEXT_MUTED};font-size:14px;">No transactions yet.</p>',
        unsafe_allow_html=True
    )
else:
    peer_stats = {}
    for tx in txns:
        if tx["status"] not in ("settled", "auto_settled"):
            continue
        is_lender    = tx["lender_username"] == username
        counterparty = tx["borrower_username"] if is_lender else tx["lender_username"]
        amount       = float(tx["amount"])

        if counterparty not in peer_stats:
            peer_stats[counterparty] = {"lent": 0, "borrowed": 0}
        if is_lender:
            peer_stats[counterparty]["lent"]     += amount
        else:
            peer_stats[counterparty]["borrowed"] += amount

    if not peer_stats:
        st.markdown(
            f'<p style="color:{TEXT_MUTED};font-size:14px;">'
            'No settled transactions yet.</p>',
            unsafe_allow_html=True
        )
    else:
        # Table header
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:40px 1fr 1fr 1fr;
                    gap:0;padding:8px 16px;
                    border-bottom:1px solid {BORDER};
                    font-size:11px;color:{TEXT_MUTED};
                    text-transform:uppercase;letter-spacing:0.06em;">
          <div>#</div>
          <div>Peer</div>
          <div style="text-align:right;">Total Exchanged</div>
          <div style="text-align:right;">Net Balance</div>
        </div>
        """, unsafe_allow_html=True)

        sorted_peers = sorted(
            peer_stats.items(),
            key=lambda x: x[1]["lent"] + x[1]["borrowed"],
            reverse=True
        )

        # Build trust lookup
        trust_lookup = {p["username"]: p["score"] for p in network}

        for i, (peer, stats) in enumerate(sorted_peers):
            total   = stats["lent"] + stats["borrowed"]
            net     = stats["lent"] - stats["borrowed"]
            net_str = f'+{fmt(net)}' if net > 0 else (f'{fmt(net)}' if net < 0 else 'KES 0')
            net_col = SUCCESS if net > 0 else (WARNING if net < 0 else TEXT_MUTED)
            initial = peer[0].upper()
            score   = trust_lookup.get(peer)
            score_html = (
                f'<span style="font-size:10px;color:{trust_color(score)};'
                f'margin-left:6px;">◆ {round(score)}</span>'
                if score is not None else ""
            )
            row_bg = BG_RAISED if i % 2 == 0 else "transparent"

            st.markdown(f"""
            <div style="display:grid;grid-template-columns:40px 1fr 1fr 1fr;
                        gap:0;padding:12px 16px;background:{row_bg};
                        border-bottom:1px solid {BORDER};align-items:center;">
              <div style="font-size:12px;color:{TEXT_MUTED};">{i+1}</div>
              <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:30px;height:30px;border-radius:50%;
                            background:{BG_SURFACE};flex-shrink:0;
                            display:flex;align-items:center;justify-content:center;
                            font-size:11px;color:{TEXT_MUTED};font-weight:600;
                            border:1px solid {BORDER};">
                  {initial}
                </div>
                <div>
                  <div style="font-size:13px;font-weight:500;color:{TEXT_PRIMARY};">
                    {peer}{score_html}
                  </div>
                  <div style="font-size:11px;color:{TEXT_MUTED};">
                    Lent {fmt(stats['lent'])} · Borrowed {fmt(stats['borrowed'])}
                  </div>
                </div>
              </div>
              <div style="text-align:right;font-size:13px;color:{TEXT_MUTED};">
                {fmt(total)}
              </div>
              <div style="text-align:right;font-size:13px;
                          font-weight:500;color:{net_col};">
                {net_str}
              </div>
            </div>
            """, unsafe_allow_html=True)

divider()

# ── Change Password ───────────────────────────────────────────
st.markdown(f"""
<div style="font-family:'DM Serif Display',Georgia,serif;
            font-size:20px;color:{TEXT_PRIMARY};margin-bottom:4px;">
  Change Password
</div>
<div style="font-size:13px;color:{TEXT_MUTED};margin-bottom:1rem;">
  Your security answer is required to confirm the change.
</div>
""", unsafe_allow_html=True)

p_left, p_right = st.columns(2)
with p_left:
    cp_email  = st.text_input("Your Email",       key="cp_email",
                               placeholder="you@example.com")
    cp_answer = st.text_input("Security Answer",  key="cp_answer",
                               placeholder="Your security answer")
with p_right:
    cp_new    = st.text_input("New Password",     key="cp_new",
                               placeholder="••••••••", type="password")
    cp_conf   = st.text_input("Confirm Password", key="cp_confirm",
                               placeholder="••••••••", type="password")

if st.button("Update Password", key="btn_update_pw"):
    if not all([cp_email, cp_answer, cp_new, cp_conf]):
        st.error("All fields are required.")
    elif cp_new != cp_conf:
        st.error("Passwords do not match.")
    else:
        try:
            api.reset_password(cp_email, cp_answer, cp_new)
            st.success("Password updated successfully.")
        except Exception as e:
            msg = getattr(getattr(e, "response", None), "json", lambda: {})()
            st.error(msg.get("detail", "Update failed."))