import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from config import (
    page_setup, require_auth, page_title, divider, sidebar_nav,
    trust_badge, trust_ring_svg, trust_color, PLOTLY_LAYOUT,
    GOLD, BG_SURFACE, BG_BASE, BG_RAISED, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    SUCCESS, DANGER, WARNING, INFO,
)
import api

page_setup("NitaRefund · Trust")
require_auth()
sidebar_nav("Trust")

username = st.session_state.get("username", "User")


@st.cache_data(ttl=30, show_spinner=False)
def load_trust(token):
    try:    network = api.get_my_network()
    except: network = []
    try:    board   = api.get_leaderboard()
    except: board   = []
    try:    history = api.get_trust_history()
    except: history = []
    return network, board, history

network, board, history = load_trust(st.session_state.token)

avg_score = (
    sum(p["score"] for p in network) / len(network)
    if network else 50.0
)
high_peers = [p for p in network if p["score"] >= 70]
low_peers  = [p for p in network if p["score"] < 40]
MEDALS     = ["🥇", "🥈", "🥉"]

# ── Header with score hero ────────────────────────────────────
page_title("Trust", "Your reputation across the peer network.")
divider()

# ── Hero row ─────────────────────────────────────────────────
hero_l, hero_m, hero_r = st.columns([3, 3, 3], gap="large")

with hero_l:
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(233,196,106,0.08) 0%,
                rgba(233,196,106,0.02) 100%);
                border:1px solid rgba(233,196,106,0.18);
                border-radius:16px;padding:24px;text-align:center;height:100%;">
      <div style="font-family:'DM Serif Display',Georgia,serif;
                  font-size:16px;color:{TEXT_SECONDARY};margin-bottom:20px;">
        Global Score
      </div>
      <div style="display:flex;justify-content:center;margin-bottom:12px;">
        {trust_ring_svg(avg_score, size=150)}
      </div>
      <div style="font-size:12px;color:{TEXT_MUTED};margin-top:8px;">
        Average across {len(network)} peer{"s" if len(network) != 1 else ""}
      </div>
    </div>
    """, unsafe_allow_html=True)

with hero_m:
    # Three mini stat cards stacked
    score_color = trust_color(avg_score)
    items = [
        ("Peers in network",  str(len(network)),   TEXT_PRIMARY),
        ("Strong trust (≥70)", str(len(high_peers)), SUCCESS),
        ("At risk (<40)",      str(len(low_peers)),  DANGER if low_peers else TEXT_MUTED),
    ]
    for label, val, color in items:
        st.markdown(f"""
        <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                    border-radius:12px;padding:14px 18px;margin-bottom:8px;
                    display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:13px;color:{TEXT_SECONDARY};">{label}</span>
          <span style="font-family:'DM Serif Display',Georgia,serif;
                       font-size:20px;color:{color};line-height:1;">{val}</span>
        </div>
        """, unsafe_allow_html=True)

with hero_r:
    st.markdown(f"""
    <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                border-radius:16px;padding:20px 22px;height:100%;">
      <div style="font-family:'DM Serif Display',Georgia,serif;
                  font-size:16px;color:{TEXT_PRIMARY};margin-bottom:16px;">
        Check Pair Trust
      </div>
      <div style="font-size:13px;color:{TEXT_MUTED};margin-bottom:14px;">
        Enter any peer's User ID to see your pairwise score.
      </div>
    """, unsafe_allow_html=True)

    peer_id = st.number_input("Peer User ID", min_value=1, step=1,
                               key="pair_id", label_visibility="collapsed")

    if st.button("Check Score", key="btn_pair"):
        try:
            result = api.get_pair_trust(int(peer_id))
            score  = float(result.get("score", 50))
            color  = trust_color(score)
            label  = "Excellent" if score >= 70 else "Good" if score >= 50 else "Fair" if score >= 25 else "Poor"
            st.markdown(f"""
            <div style="background:rgba(233,196,106,0.05);
                        border:1px solid rgba(233,196,106,0.15);
                        border-radius:10px;padding:14px;text-align:center;
                        margin-top:10px;">
              <div style="font-size:11px;color:{TEXT_MUTED};
                          text-transform:uppercase;letter-spacing:0.06em;
                          margin-bottom:6px;">Score with User {int(peer_id)}</div>
              <div style="font-size:40px;font-family:'DM Serif Display',Georgia,serif;
                          color:{color};line-height:1;">{round(score)}</div>
              <div style="font-size:12px;color:{color};margin-top:4px;">{label}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.error("No trust record found for that User ID.")

    st.markdown('</div>', unsafe_allow_html=True)

divider()

# ── Trust trend chart ─────────────────────────────────────────
st.markdown(f"""
<div style="font-family:'DM Serif Display',Georgia,serif;
            font-size:20px;color:{TEXT_PRIMARY};margin-bottom:4px;">
  Trust Trend
</div>
<div style="font-size:13px;color:{TEXT_MUTED};margin-bottom:1rem;">
  How your score has evolved over time as transactions settle.
</div>
""", unsafe_allow_html=True)

if len(history) > 1:
    dates  = [h["date"] for h in history]
    scores = [h["score"] for h in history]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=scores,
        mode="lines+markers",
        line=dict(color=GOLD, width=2.5),
        marker=dict(color=GOLD, size=7,
                    line=dict(color=BG_BASE, width=2)),
        fill="tozeroy",
        fillcolor="rgba(233,196,106,0.06)",
        hovertemplate="%{x}<br>Score: %{y}<extra></extra>",
    ))
    # Reference lines
    fig.add_hline(y=70, line_dash="dot", line_color=SUCCESS,
                  line_width=1, opacity=0.4,
                  annotation_text="Excellent",
                  annotation_font_color=SUCCESS,
                  annotation_font_size=10)
    fig.add_hline(y=40, line_dash="dot", line_color=WARNING,
                  line_width=1, opacity=0.4,
                  annotation_text="At risk",
                  annotation_font_color=WARNING,
                  annotation_font_size=10)
    layout = dict(PLOTLY_LAYOUT)
    layout.update(
        height=240,
        yaxis=dict(range=[0, 100], gridcolor=BG_RAISED,
                   zerolinecolor=BG_RAISED, ticksuffix="  "),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        margin=dict(l=10, r=60, t=10, b=30),
    )
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.markdown(f"""
    <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                border-radius:12px;padding:2rem;text-align:center;">
      <div style="font-size:13px;color:{TEXT_MUTED};">
        Not enough history yet. Complete more transactions to see your trend.
      </div>
    </div>
    """, unsafe_allow_html=True)

divider()

# ── Network + Leaderboard ─────────────────────────────────────
net_col, board_col = st.columns([5, 5], gap="large")

with net_col:
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;
                align-items:baseline;margin-bottom:12px;">
      <div style="font-family:'DM Serif Display',Georgia,serif;
                  font-size:20px;color:{TEXT_PRIMARY};">Your Network</div>
      <div style="font-size:12px;color:{TEXT_MUTED};">{len(network)} peers</div>
    </div>
    """, unsafe_allow_html=True)

    if not network:
        st.markdown(f"""
        <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                    border-radius:14px;padding:3rem;text-align:center;">
          <div style="font-size:32px;margin-bottom:12px;">🤝</div>
          <div style="font-size:14px;color:{TEXT_MUTED};">
            No peers yet. Complete transactions to build your network.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="background:{BG_SURFACE};border:1px solid {BORDER};'
            f'border-radius:14px;overflow:hidden;">',
            unsafe_allow_html=True
        )
        for i, peer in enumerate(network):
            score   = float(peer["score"])
            color   = trust_color(score)
            border  = f"border-bottom:1px solid {BORDER};" if i < len(network) - 1 else ""
            initial = peer["username"][0].upper()

            # Mini progress bar fill
            bar_pct = int(score)
            bar_color = trust_color(score)

            st.markdown(f"""
            <div style="padding:13px 18px;{border}">
              <div style="display:flex;align-items:center;gap:12px;margin-bottom:7px;">
                <div style="width:34px;height:34px;border-radius:50%;
                            background:{BG_RAISED};flex-shrink:0;
                            display:flex;align-items:center;justify-content:center;
                            font-size:13px;color:{color};font-weight:600;
                            border:1px solid {BORDER};">
                  {initial}
                </div>
                <div style="flex:1;font-size:13px;font-weight:500;
                            color:{TEXT_PRIMARY};">
                  {peer["username"]}
                </div>
                <div style="font-family:'DM Serif Display',Georgia,serif;
                            font-size:18px;color:{color};line-height:1;
                            margin-right:8px;">
                  {round(score)}
                </div>
                <div>{trust_badge(score)}</div>
              </div>
              <div style="background:{BG_RAISED};border-radius:9999px;
                          height:3px;margin-left:46px;overflow:hidden;">
                <div style="width:{bar_pct}%;height:100%;
                            background:{bar_color};border-radius:9999px;
                            opacity:0.6;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


with board_col:
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;
                align-items:baseline;margin-bottom:12px;">
      <div style="font-family:'DM Serif Display',Georgia,serif;
                  font-size:20px;color:{TEXT_PRIMARY};">Global Leaderboard</div>
      <div style="font-size:12px;color:{TEXT_MUTED};">Top 10</div>
    </div>
    """, unsafe_allow_html=True)

    if not board:
        st.markdown(
            f'<p style="color:{TEXT_MUTED};font-size:14px;">No data yet.</p>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="background:{BG_SURFACE};border:1px solid {BORDER};'
            f'border-radius:14px;overflow:hidden;">',
            unsafe_allow_html=True
        )
        for i, entry in enumerate(board):
            score  = round(float(entry.get("score", 0)))
            uname  = entry.get("username", "—")
            tx_cnt = entry.get("transaction_count", 0)
            color  = trust_color(score)
            border = f"border-bottom:1px solid {BORDER};" if i < len(board) - 1 else ""
            is_me  = uname == username
            row_bg = "rgba(233,196,106,0.04)" if is_me else "transparent"

            rank = (
                f'<span style="font-size:18px;line-height:1;">{MEDALS[i]}</span>'
                if i < 3 else
                f'<span style="font-size:12px;color:{TEXT_MUTED};'
                f'font-weight:500;">#{i+1}</span>'
            )
            you_tag = (
                f'<span style="font-size:10px;color:{GOLD};'
                f'background:rgba(233,196,106,0.12);border-radius:4px;'
                f'padding:1px 5px;margin-left:6px;">you</span>'
                if is_me else ""
            )

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;
                        padding:12px 18px;{border}background:{row_bg};">
              <div style="width:28px;text-align:center;flex-shrink:0;">{rank}</div>
              <div style="flex:1;min-width:0;">
                <div style="font-size:13px;font-weight:500;color:{TEXT_PRIMARY};">
                  {uname}{you_tag}
                </div>
                <div style="font-size:11px;color:{TEXT_MUTED};margin-top:1px;">
                  {tx_cnt} transaction{"s" if tx_cnt != 1 else ""}
                </div>
              </div>
              <div style="font-family:'DM Serif Display',Georgia,serif;
                          font-size:20px;color:{color};line-height:1;">
                {score}
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)