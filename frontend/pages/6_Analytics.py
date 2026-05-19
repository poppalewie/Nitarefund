import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from config import (
    page_setup, require_auth, page_title, divider, sidebar_nav,
    stat_card, fmt, trust_color, PLOTLY_LAYOUT,
    GOLD, BG_BASE, BG_SURFACE, BG_RAISED, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    SUCCESS, DANGER, WARNING, INFO,
)
import api

page_setup("NitaRefund · Analytics")
require_auth()
sidebar_nav("Analytics")

username = st.session_state.get("username", "User")


@st.cache_data(ttl=60, show_spinner=False)
def load_analytics(token):
    try:    txns       = api.get_my_transactions(limit=100)
    except: txns       = []
    try:    categories = api.get_spending_categories()
    except: categories = []
    try:    network    = api.get_my_network()
    except: network    = []
    try:    balance    = api.get_wallet_balance()
    except: balance    = 0.0
    try:    summary    = api.get_summary()
    except: summary    = {"total_lent":0,"total_borrowed":0,
                          "pending_count":0,"total_count":0}
    return txns, categories, network, balance, summary

txns, categories, network, balance, summary = load_analytics(st.session_state.token)

page_title("Analytics", "Insights into your spending, lending, and trust behaviour.")
divider()

# ── Top stat row ──────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
avg_score = (sum(p["score"] for p in network)/len(network) if network else 50.0)
net       = summary["total_lent"] - summary["total_borrowed"]
net_label = "Net Lender" if net >= 0 else "Net Borrower"

with c1: stat_card("Wallet Balance",    fmt(balance), accent=True)
with c2: stat_card("Total Volume",
                   fmt(summary["total_lent"] + summary["total_borrowed"]))
with c3: stat_card("Trust Score",       str(round(avg_score)))
with c4: stat_card("Net Position",      fmt(abs(net)), sub=net_label,
                   accent=net >= 0)

divider()

# ── Row 1: Spending categories + monthly volume ───────────────
row1_l, row1_r = st.columns(2, gap="large")

with row1_l:
    st.markdown(f"""
    <div style="font-family:'DM Serif Display',Georgia,serif;
                font-size:20px;color:{TEXT_PRIMARY};margin-bottom:4px;">
      Spending by Category
    </div>
    <div style="font-size:13px;color:{TEXT_MUTED};margin-bottom:1rem;">
      Based on transaction descriptions across all settled activity.
    </div>
    """, unsafe_allow_html=True)

    if not categories:
        st.markdown(
            f'<div style="background:{BG_SURFACE};border:1px solid {BORDER};'
            f'border-radius:14px;padding:3rem;text-align:center;">'
            f'<div style="font-size:32px;margin-bottom:10px;">📊</div>'
            f'<div style="font-size:13px;color:{TEXT_MUTED};">No settled transactions yet.</div>'
            f'</div>', unsafe_allow_html=True
        )
    else:
        CAT_COLORS = {
            "Food & Drink":  "#E9C46A",
            "Transport":     "#6098e0",
            "Rent & Bills":  "#e06060",
            "Shopping":      "#e0a060",
            "Entertainment": "#52c48a",
            "Services":      "#a06098",
            "Education":     "#60c4c4",
            "Other":         "#484848",
        }
        labels = [c["category"] for c in categories]
        values = [c["amount"]   for c in categories]
        colors = [CAT_COLORS.get(l, GOLD) for l in labels]

        fig = go.Figure(go.Pie(
            labels=labels, values=values,
            marker_colors=colors,
            hole=0.6,
            textinfo="label+percent",
            textfont_size=11,
            hovertemplate="%{label}<br>%{customdata}<extra></extra>",
            customdata=[fmt(v) for v in values],
        ))
        layout = dict(PLOTLY_LAYOUT)
        layout.update(
            height=300,
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            annotations=[dict(
                text=f"<b>{fmt(sum(values))}</b>",
                x=0.5, y=0.5, font_size=14,
                font_color=TEXT_PRIMARY,
                showarrow=False
            )]
        )
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

        # Category list below chart
        st.markdown(
            f'<div style="background:{BG_SURFACE};border:1px solid {BORDER};'
            f'border-radius:12px;overflow:hidden;">',
            unsafe_allow_html=True
        )
        for i, cat in enumerate(categories):
            color  = CAT_COLORS.get(cat["category"], GOLD)
            pct    = round(cat["amount"] / sum(values) * 100) if values else 0
            border = f"border-bottom:1px solid {BORDER};" if i < len(categories)-1 else ""
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;
                        padding:10px 16px;{border}">
              <div style="width:10px;height:10px;border-radius:50%;
                          background:{color};flex-shrink:0;"></div>
              <div style="flex:1;font-size:13px;color:{TEXT_PRIMARY};">
                {cat["category"]}
              </div>
              <div style="font-size:13px;color:{TEXT_MUTED};">{pct}%</div>
              <div style="font-size:13px;font-weight:500;color:{TEXT_PRIMARY};
                          font-family:'DM Serif Display',Georgia,serif;">
                {fmt(cat["amount"])}
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


with row1_r:
    st.markdown(f"""
    <div style="font-family:'DM Serif Display',Georgia,serif;
                font-size:20px;color:{TEXT_PRIMARY};margin-bottom:4px;">
      Monthly Volume
    </div>
    <div style="font-size:13px;color:{TEXT_MUTED};margin-bottom:1rem;">
      Total amount lent and borrowed each month.
    </div>
    """, unsafe_allow_html=True)

    if not txns:
        st.markdown(
            f'<div style="background:{BG_SURFACE};border:1px solid {BORDER};'
            f'border-radius:14px;padding:3rem;text-align:center;">'
            f'<div style="font-size:13px;color:{TEXT_MUTED};">No data yet.</div>'
            f'</div>', unsafe_allow_html=True
        )
    else:
        monthly = {}
        for tx in txns:
            try:
                dt    = datetime.fromisoformat(tx["created_at"].replace("Z","+00:00"))
                month = dt.strftime("%b %Y")
                if month not in monthly:
                    monthly[month] = {"lent": 0, "borrowed": 0, "count": 0}
                if tx["lender_username"] == username:
                    monthly[month]["lent"] += float(tx["amount"])
                else:
                    monthly[month]["borrowed"] += float(tx["amount"])
                monthly[month]["count"] += 1
            except Exception:
                pass

        months        = list(monthly.keys())
        lent_vals     = [monthly[m]["lent"]     for m in months]
        borrowed_vals = [monthly[m]["borrowed"] for m in months]
        count_vals    = [monthly[m]["count"]    for m in months]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Lent", x=months, y=lent_vals,
            marker_color=SUCCESS, marker_opacity=0.85,
            hovertemplate="%{x}<br>Lent: %{customdata}<extra></extra>",
            customdata=[fmt(v) for v in lent_vals],
        ))
        fig.add_trace(go.Bar(
            name="Borrowed", x=months, y=borrowed_vals,
            marker_color=WARNING, marker_opacity=0.85,
            hovertemplate="%{x}<br>Borrowed: %{customdata}<extra></extra>",
            customdata=[fmt(v) for v in borrowed_vals],
        ))
        layout = dict(PLOTLY_LAYOUT)
        layout.update(
            height=300, barmode="group",
            legend=dict(orientation="h", y=1.1),
            margin=dict(l=10, r=10, t=30, b=20),
        )
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

        # Peak month callout
        if monthly:
            peak_month = max(monthly, key=lambda m: monthly[m]["lent"]+monthly[m]["borrowed"])
            peak_total = monthly[peak_month]["lent"] + monthly[peak_month]["borrowed"]
            st.markdown(f"""
            <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                        border-radius:10px;padding:12px 16px;
                        display:flex;justify-content:space-between;align-items:center;">
              <span style="font-size:13px;color:{TEXT_MUTED};">Peak month</span>
              <span style="font-size:13px;font-weight:500;color:{TEXT_PRIMARY};">
                {peak_month} — {fmt(peak_total)}
              </span>
            </div>
            """, unsafe_allow_html=True)

divider()

# ── Row 2: Peer analysis ──────────────────────────────────────
st.markdown(f"""
<div style="font-family:'DM Serif Display',Georgia,serif;
            font-size:20px;color:{TEXT_PRIMARY};margin-bottom:4px;">
  Peer Analysis
</div>
<div style="font-size:13px;color:{TEXT_MUTED};margin-bottom:1rem;">
  Your top counterparties by total transaction volume, with trust scores.
</div>
""", unsafe_allow_html=True)

if txns:
    peer_stats = {}
    for tx in txns:
        is_lender    = tx["lender_username"] == username
        counterparty = tx["borrower_username"] if is_lender else tx["lender_username"]
        amount       = float(tx["amount"])
        if counterparty not in peer_stats:
            peer_stats[counterparty] = {"lent":0, "borrowed":0, "count":0,
                                         "settled":0, "disputed":0}
        if is_lender:
            peer_stats[counterparty]["lent"] += amount
        else:
            peer_stats[counterparty]["borrowed"] += amount
        peer_stats[counterparty]["count"] += 1
        if tx["status"] in ("settled","auto_settled"):
            peer_stats[counterparty]["settled"] += 1
        if tx["status"] == "disputed":
            peer_stats[counterparty]["disputed"] += 1

    trust_lookup = {p["username"]: p["score"] for p in network}
    sorted_peers = sorted(
        peer_stats.items(),
        key=lambda x: x[1]["lent"] + x[1]["borrowed"],
        reverse=True
    )[:10]

    if sorted_peers:
        # Bar chart
        peer_names    = [p[0] for p in sorted_peers]
        peer_lent     = [p[1]["lent"]     for p in sorted_peers]
        peer_borrowed = [p[1]["borrowed"] for p in sorted_peers]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Lent",     x=peer_names, y=peer_lent,
            marker_color=SUCCESS, marker_opacity=0.8,
        ))
        fig.add_trace(go.Bar(
            name="Borrowed", x=peer_names, y=peer_borrowed,
            marker_color=WARNING, marker_opacity=0.8,
        ))
        layout = dict(PLOTLY_LAYOUT)
        layout.update(
            height=260, barmode="group",
            legend=dict(orientation="h", y=1.1),
            margin=dict(l=10, r=10, t=30, b=20),
            title="Volume per Peer",
        )
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

        # Peer table
        st.markdown(
            f'<div style="background:{BG_SURFACE};border:1px solid {BORDER};'
            f'border-radius:14px;overflow:hidden;">',
            unsafe_allow_html=True
        )

        # Header
        st.markdown(f"""
        <div style="display:grid;
                    grid-template-columns:30px 1fr 100px 100px 80px 60px 70px;
                    gap:0;padding:8px 16px;border-bottom:1px solid {BORDER};
                    font-size:11px;color:{TEXT_MUTED};
                    text-transform:uppercase;letter-spacing:0.06em;">
          <div>#</div><div>Peer</div><div style="text-align:right;">Lent</div>
          <div style="text-align:right;">Borrowed</div>
          <div style="text-align:right;">Txns</div>
          <div style="text-align:right;">Trust</div>
          <div style="text-align:right;">Settled%</div>
        </div>
        """, unsafe_allow_html=True)

        for i, (peer, stats) in enumerate(sorted_peers):
            score      = trust_lookup.get(peer)
            score_str  = str(round(score)) if score is not None else "—"
            score_col  = trust_color(score) if score is not None else TEXT_MUTED
            settle_pct = (round(stats["settled"]/stats["count"]*100)
                          if stats["count"] else 0)
            settle_col = SUCCESS if settle_pct >= 80 else (WARNING if settle_pct >= 40 else DANGER)
            row_bg     = BG_RAISED if i % 2 == 0 else "transparent"
            border     = f"border-bottom:1px solid {BORDER};" if i < len(sorted_peers)-1 else ""
            initial    = peer[0].upper()

            st.markdown(f"""
            <div style="display:grid;
                        grid-template-columns:30px 1fr 100px 100px 80px 60px 70px;
                        gap:0;padding:11px 16px;background:{row_bg};{border}
                        align-items:center;">
              <div style="font-size:12px;color:{TEXT_MUTED};">{i+1}</div>
              <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:28px;height:28px;border-radius:50%;
                            background:{BG_SURFACE};flex-shrink:0;
                            display:flex;align-items:center;justify-content:center;
                            font-size:11px;color:{TEXT_MUTED};font-weight:600;
                            border:1px solid {BORDER};">
                  {initial}
                </div>
                <span style="font-size:13px;font-weight:500;color:{TEXT_PRIMARY};">
                  {peer}
                </span>
                {'<span style="font-size:10px;color:'+DANGER+';margin-left:4px;">⚠</span>' if stats["disputed"] > 0 else ''}
              </div>
              <div style="text-align:right;font-size:13px;color:{SUCCESS};">
                {fmt(stats["lent"])}
              </div>
              <div style="text-align:right;font-size:13px;color:{WARNING};">
                {fmt(stats["borrowed"])}
              </div>
              <div style="text-align:right;font-size:13px;color:{TEXT_MUTED};">
                {stats["count"]}
              </div>
              <div style="text-align:right;font-size:13px;
                          font-weight:500;color:{score_col};">
                {score_str}
              </div>
              <div style="text-align:right;font-size:13px;color:{settle_col};">
                {settle_pct}%
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

divider()

# ── Row 3: Activity heatmap by day of week ────────────────────
st.markdown(f"""
<div style="font-family:'DM Serif Display',Georgia,serif;
            font-size:20px;color:{TEXT_PRIMARY};margin-bottom:4px;">
  Activity Patterns
</div>
<div style="font-size:13px;color:{TEXT_MUTED};margin-bottom:1rem;">
  When you tend to transact most.
</div>
""", unsafe_allow_html=True)

if txns:
    pat_l, pat_r = st.columns(2, gap="large")

    with pat_l:
        dow_counts = {d: 0 for d in
                      ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]}
        for tx in txns:
            try:
                dt  = datetime.fromisoformat(tx["created_at"].replace("Z","+00:00"))
                day = dt.strftime("%a")
                if day in dow_counts:
                    dow_counts[day] += 1
            except Exception:
                pass

        days   = list(dow_counts.keys())
        counts = list(dow_counts.values())
        colors = [GOLD if c == max(counts) else BG_RAISED for c in counts]

        fig = go.Figure(go.Bar(
            x=days, y=counts,
            marker_color=colors,
            marker_line_width=0,
            hovertemplate="%{x}: %{y} transactions<extra></extra>",
        ))
        layout = dict(PLOTLY_LAYOUT)
        layout.update(
            height=220, title="Transactions by Day of Week",
            showlegend=False,
            margin=dict(l=10, r=10, t=40, b=20),
            yaxis=dict(gridcolor=BG_RAISED, zerolinecolor=BG_RAISED),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

    with pat_r:
        # Status breakdown donut
        status_counts = {}
        for tx in txns:
            s = tx["status"].replace("_"," ").capitalize()
            status_counts[s] = status_counts.get(s, 0) + 1

        STATUS_COLORS = {
            "Pending": WARNING, "Approved": INFO,
            "Awaiting confirmation": GOLD, "Settled": SUCCESS,
            "Auto settled": SUCCESS, "Rejected": DANGER,
            "Cancelled": "#666", "Disputed": DANGER,
        }
        labels = list(status_counts.keys())
        values = list(status_counts.values())
        colors = [STATUS_COLORS.get(l, GOLD) for l in labels]

        fig = go.Figure(go.Pie(
            labels=labels, values=values,
            marker_colors=colors, hole=0.55,
            textinfo="label+percent", textfont_size=11,
        ))
        layout = dict(PLOTLY_LAYOUT)
        layout.update(
            height=220, showlegend=False, title="Transaction Status Mix",
            margin=dict(l=10, r=10, t=40, b=10),
        )
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

divider()

# ── Wallet Leaderboard ────────────────────────────────────────
st.markdown(f"""
<div style="font-family:'DM Serif Display',Georgia,serif;
            font-size:20px;color:{TEXT_PRIMARY};margin-bottom:4px;">
  Wallet Leaderboard
</div>
<div style="font-size:13px;color:{TEXT_MUTED};margin-bottom:1rem;">
  Earned through reciprocal transactions — the more you give back, the
  more surplus accumulates. You can be #1 in trust and #6 here, or vice versa.
</div>
""", unsafe_allow_html=True)

try:
    w_board = api.get_wallet_leaderboard()
except Exception:
    w_board = []

MEDALS = ["🥇", "🥈", "🥉"]

w_left, w_right = st.columns([5, 5], gap="large")

with w_left:
    if not w_board:
        st.markdown(
            f'<div style="background:{BG_SURFACE};border:1px solid {BORDER};'
            f'border-radius:14px;padding:2rem;text-align:center;">'
            f'<div style="font-size:13px;color:{TEXT_MUTED};">No wallet data yet.</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="background:{BG_SURFACE};border:1px solid {BORDER};'
            f'border-radius:14px;overflow:hidden;">',
            unsafe_allow_html=True
        )
        for i, entry in enumerate(w_board):
            uname  = entry.get("username", "—")
            bal    = float(entry.get("balance", 0))
            is_me  = uname == username
            row_bg = "rgba(233,196,106,0.04)" if is_me else "transparent"
            border = f"border-bottom:1px solid {BORDER};" if i < len(w_board)-1 else ""
            initial = uname[0].upper()
            you_tag = (
                f'<span style="font-size:10px;color:{GOLD};'
                f'background:rgba(233,196,106,0.12);border-radius:4px;'
                f'padding:1px 5px;margin-left:6px;">you</span>'
                if is_me else ""
            )
            if i < 3:
                rank_html = f'<span style="font-size:18px;line-height:1;">{MEDALS[i]}</span>'
            else:
                rank_html = f'<span style="font-size:12px;color:{TEXT_MUTED};font-weight:500;">#{i+1}</span>'

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;
                        padding:13px 18px;{border}background:{row_bg};">
              <div style="width:28px;text-align:center;flex-shrink:0;">
                {rank_html}
              </div>
              <div style="width:32px;height:32px;border-radius:50%;
                          background:{BG_RAISED};flex-shrink:0;
                          display:flex;align-items:center;justify-content:center;
                          font-size:12px;color:{TEXT_MUTED};font-weight:600;
                          border:1px solid {BORDER};">
                {initial}
              </div>
              <div style="flex:1;font-size:13px;font-weight:500;color:{TEXT_PRIMARY};">
                {uname}{you_tag}
              </div>
              <div style="font-family:'DM Serif Display',Georgia,serif;
                          font-size:18px;color:{GOLD};line-height:1;">
                {fmt(bal)}
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with w_right:
    # Bar chart of wallet balances
    if w_board:
        names    = [e["username"] for e in w_board]
        balances = [float(e["balance"]) for e in w_board]
        bar_colors = [
            "rgba(233,196,106,0.9)" if n == username else "rgba(233,196,106,0.35)"
            for n in names
        ]

        fig = go.Figure(go.Bar(
            x=names, y=balances,
            marker_color=bar_colors,
            marker_line_width=0,
            hovertemplate="%{x}<br>%{customdata}<extra></extra>",
            customdata=[fmt(b) for b in balances],
        ))
        layout = dict(PLOTLY_LAYOUT)
        layout.update(
            height=320,
            showlegend=False,
            title="Wallet Balances",
            margin=dict(l=10, r=10, t=40, b=20),
            yaxis=dict(gridcolor=BG_RAISED, zerolinecolor=BG_RAISED),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(
            f'<p style="color:{TEXT_MUTED};font-size:14px;padding:2rem 0;'
            f'text-align:center;">No wallet data yet.</p>',
            unsafe_allow_html=True
        )