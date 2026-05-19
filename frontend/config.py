import streamlit as st

API_URL = "http://127.0.0.1:8000"

# ── Design tokens ─────────────────────────────────────────────
GOLD           = "#E9C46A"
GOLD_DIM       = "#C9A44A"
BG_BASE        = "#080808"
BG_SURFACE     = "#101010"
BG_RAISED      = "#171717"
BG_HOVER       = "#1e1e1e"
TEXT_PRIMARY   = "#f0f0f0"
TEXT_SECONDARY = "#888888"
TEXT_MUTED     = "#484848"
BORDER         = "rgba(255,255,255,0.07)"
BORDER_HOVER   = "rgba(255,255,255,0.13)"
SUCCESS        = "#52c48a"
DANGER         = "#e06060"
WARNING        = "#e0a060"
INFO           = "#6098e0"
PRIMARY        = GOLD

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT_PRIMARY, family="DM Sans, sans-serif"),
    xaxis=dict(gridcolor=BG_RAISED, zerolinecolor=BG_RAISED),
    yaxis=dict(gridcolor=BG_RAISED, zerolinecolor=BG_RAISED),
    margin=dict(l=20, r=20, t=40, b=20),
)


# ── Page config ───────────────────────────────────────────────
def page_setup(title="NitaRefund", layout="wide"):
    st.set_page_config(
        page_title=title,
        page_icon="💛",
        layout=layout,
        initial_sidebar_state="collapsed",
    )
    inject_css()


# ── Auth guard ────────────────────────────────────────────────
def require_auth():
    if not st.session_state.get("token"):
        st.switch_page("app.py")


# ── CSS ───────────────────────────────────────────────────────
def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&family=DM+Serif+Display&display=swap');

    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif !important;
        background-color: {BG_BASE} !important;
        color: {TEXT_PRIMARY} !important;
    }}
    .stApp {{ background-color: {BG_BASE} !important; }}
    #MainMenu, footer, header {{ visibility: hidden !important; }}
    [data-testid="stSidebarNav"] {{ display: none !important; }}

    /* ── Main container ── */
    .main .block-container {{
        padding: 2rem 2.5rem !important;
        max-width: 1260px !important;
    }}

    /* ── Stat cards ── */
    .pl-stat {{
        background: {BG_RAISED};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 18px 20px;
    }}
    .pl-stat.accent {{
        background: rgba(233,196,106,0.06);
        border-color: rgba(233,196,106,0.20);
    }}
    .pl-stat .stat-label {{
        font-size: 11px;
        color: {TEXT_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 8px;
    }}
    .pl-stat .stat-value {{
        font-size: 22px;
        font-weight: 400;
        color: {TEXT_PRIMARY};
        font-family: 'DM Serif Display', Georgia, serif;
        letter-spacing: -0.02em;
        line-height: 1;
    }}
    .pl-stat.accent .stat-value {{ color: {GOLD}; }}
    .pl-stat .stat-sub {{
        font-size: 12px;
        color: {TEXT_MUTED};
        margin-top: 6px;
    }}

    /* ── Badges ── */
    .badge {{
        display: inline-flex;
        align-items: center;
        padding: 2px 9px;
        font-size: 11.5px;
        font-weight: 500;
        border-radius: 9999px;
        white-space: nowrap;
    }}
    .badge-pending               {{ background:rgba(224,160,96,0.10);  color:{WARNING}; border:1px solid rgba(224,160,96,0.22); }}
    .badge-awaiting_confirmation {{ background:rgba(233,196,106,0.10); color:{GOLD};    border:1px solid rgba(233,196,106,0.22); }}
    .badge-approved              {{ background:rgba(96,152,224,0.10);  color:{INFO};    border:1px solid rgba(96,152,224,0.22); }}
    .badge-settled               {{ background:rgba(82,196,138,0.10);  color:{SUCCESS}; border:1px solid rgba(82,196,138,0.22); }}
    .badge-auto_settled          {{ background:rgba(82,196,138,0.10);  color:{SUCCESS}; border:1px solid rgba(82,196,138,0.22); }}
    .badge-rejected              {{ background:rgba(224,96,96,0.10);   color:{DANGER};  border:1px solid rgba(224,96,96,0.22); }}
    .badge-cancelled             {{ background:rgba(120,120,120,0.10); color:#777;      border:1px solid rgba(120,120,120,0.22); }}
    .badge-disputed              {{ background:rgba(224,96,96,0.10);   color:{DANGER};  border:1px solid rgba(224,96,96,0.22); }}

    /* ── Trust badges ── */
    .trust-high {{ background:rgba(82,196,138,0.10);  color:{SUCCESS}; border:1px solid rgba(82,196,138,0.22);  border-radius:9999px; padding:2px 9px; font-size:11.5px; font-weight:500; }}
    .trust-mid  {{ background:rgba(233,196,106,0.10); color:{GOLD};    border:1px solid rgba(233,196,106,0.22); border-radius:9999px; padding:2px 9px; font-size:11.5px; font-weight:500; }}
    .trust-low  {{ background:rgba(224,96,96,0.10);   color:{DANGER};  border:1px solid rgba(224,96,96,0.22);   border-radius:9999px; padding:2px 9px; font-size:11.5px; font-weight:500; }}

    /* ── Primary button ── */
    .stButton > button {{
        background: {GOLD} !important;
        color: #0a0a0a !important;
        border: none !important;
        border-radius: 9px !important;
        font-weight: 600 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        padding: 10px 20px !important;
        transition: all 160ms ease !important;
        letter-spacing: -0.01em !important;
        width: 100% !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(233,196,106,0.22) !important;
    }}
    .stButton > button:active {{ transform: translateY(0) !important; }}

    .btn-ghost > button {{
        background: {BG_RAISED} !important;
        color: {TEXT_PRIMARY} !important;
        border: 1px solid {BORDER_HOVER} !important;
        box-shadow: none !important;
    }}
    .btn-ghost > button:hover {{
        background: {BG_HOVER} !important;
        box-shadow: none !important;
        transform: none !important;
    }}
    .btn-danger > button {{
        background: rgba(224,96,96,0.12) !important;
        color: {DANGER} !important;
        border: 1px solid rgba(224,96,96,0.28) !important;
        box-shadow: none !important;
    }}
    .btn-danger > button:hover {{
        background: rgba(224,96,96,0.20) !important;
        box-shadow: none !important;
        transform: none !important;
    }}

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stTextArea > div > textarea {{
        background: {BG_RAISED} !important;
        border: 1px solid {BORDER} !important;
        color: {TEXT_PRIMARY} !important;
        border-radius: 9px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        padding: 9px 12px !important;
    }}
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: rgba(233,196,106,0.40) !important;
        box-shadow: 0 0 0 3px rgba(233,196,106,0.07) !important;
    }}
    .stTextInput label, .stNumberInput label,
    .stDateInput label, .stTextArea label, .stSelectbox label {{
        font-size: 13px !important;
        font-weight: 500 !important;
        color: {TEXT_PRIMARY} !important;
    }}

    /* ── Selectbox ── */
    .stSelectbox > div > div {{
        background: {BG_RAISED} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 9px !important;
        color: {TEXT_PRIMARY} !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        background: transparent !important;
        border-bottom: 1px solid {BORDER} !important;
        gap: 0 !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        color: {TEXT_SECONDARY} !important;
        border-radius: 0 !important;
        padding: 10px 22px !important;
        font-size: 14px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {TEXT_PRIMARY} !important;
        border-bottom: 2px solid {GOLD} !important;
    }}
    .stTabs [data-baseweb="tab-panel"] {{ padding: 1rem 0 0 !important; }}

    /* ── Expander ── */
    .streamlit-expanderHeader {{
        background: {BG_SURFACE} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 12px !important;
        color: {TEXT_PRIMARY} !important;
        font-size: 14px !important;
    }}
    .streamlit-expanderContent {{
        background: {BG_SURFACE} !important;
        border: 1px solid {BORDER} !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 16px 20px !important;
    }}

    /* ── Alert messages ── */
    .stSuccess {{ background: rgba(82,196,138,0.08)  !important; border-color: rgba(82,196,138,0.20)  !important; border-radius: 9px !important; }}
    .stError   {{ background: rgba(224,96,96,0.08)   !important; border-color: rgba(224,96,96,0.20)   !important; border-radius: 9px !important; }}
    .stWarning {{ background: rgba(224,160,96,0.08)  !important; border-color: rgba(224,160,96,0.20)  !important; border-radius: 9px !important; }}
    .stInfo    {{ background: rgba(96,152,224,0.08)  !important; border-color: rgba(96,152,224,0.20)  !important; border-radius: 9px !important; }}

    /* ── Page titles ── */
    .pl-title {{
        font-family: 'DM Serif Display', Georgia, serif;
        font-size: 30px;
        color: {TEXT_PRIMARY};
        letter-spacing: -0.01em;
        line-height: 1.1;
        margin-bottom: 4px;
    }}
    .pl-subtitle {{
        font-size: 14px;
        color: {TEXT_SECONDARY};
        margin-bottom: 1.5rem;
    }}
    .pl-divider {{
        border: none;
        border-top: 1px solid {BORDER};
        margin: 1.25rem 0;
    }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar        {{ width: 4px; height: 4px; }}
    ::-webkit-scrollbar-track  {{ background: transparent; }}
    ::-webkit-scrollbar-thumb  {{ background: {BORDER_HOVER}; border-radius: 2px; }}

    /* ── Columns ── */
    [data-testid="column"] {{ padding: 0 10px !important; }}
    [data-testid="column"]:first-child {{ padding-left: 0 !important; }}
    [data-testid="column"]:last-child  {{ padding-right: 0 !important; }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(160deg, #0e0e0e 0%, {BG_BASE} 100%) !important;
        border-right: 1px solid {BORDER} !important;
        padding-top: 0 !important;
    }}
    section[data-testid="stSidebar"] > div {{
        padding-top: 0 !important;
    }}

    /* Sidebar nav buttons */
    section[data-testid="stSidebar"] .stButton > button {{
        background: transparent !important;
        color: {TEXT_SECONDARY} !important;
        border: none !important;
        border-radius: 8px !important;
        text-align: left !important;
        font-weight: 400 !important;
        font-size: 14px !important;
        padding: 9px 14px !important;
        width: 100% !important;
        box-shadow: none !important;
        transform: none !important;
        letter-spacing: 0 !important;
        transition: background 120ms, color 120ms !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: {BG_RAISED} !important;
        color: {TEXT_PRIMARY} !important;
        transform: none !important;
        box-shadow: none !important;
    }}
    section[data-testid="stSidebar"] .nav-active > button {{
        background: rgba(233,196,106,0.08) !important;
        color: {GOLD} !important;
        font-weight: 500 !important;
    }}
    section[data-testid="stSidebar"] .btn-ghost > button {{
        background: transparent !important;
        color: {TEXT_MUTED} !important;
        border: none !important;
        font-size: 13px !important;
    }}
    section[data-testid="stSidebar"] .btn-ghost > button:hover {{
        background: {BG_RAISED} !important;
        color: {DANGER} !important;
    }}
    </style>
    """, unsafe_allow_html=True)


# ── Sidebar nav ───────────────────────────────────────────────
def sidebar_nav(active=""):
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:1.5rem 1.2rem 0.75rem;">
          <div style="font-family:'DM Serif Display',Georgia,serif;
                      font-size:22px;color:{GOLD};
                      letter-spacing:-0.01em;line-height:1;margin-bottom:6px;">
            NitaRefund
          </div>
          <div style="display:flex;align-items:center;gap:6px;">
            <div style="width:6px;height:6px;border-radius:50%;
                        background:{SUCCESS};"></div>
            <span style="font-size:12px;color:{TEXT_MUTED};">
              {st.session_state.get('username', '')}
            </span>
          </div>
        </div>
        <div style="border-top:1px solid {BORDER};margin:0 1rem 0.5rem;"></div>
        <div style="font-size:10px;color:{TEXT_MUTED};text-transform:uppercase;
                    letter-spacing:0.08em;padding:0 1.2rem 4px;">
          Navigation
        </div>
        """, unsafe_allow_html=True)

        pages = [
            ("Dashboard",    "pages/1_Dashboard.py"),
            ("Transactions", "pages/2_Transactions.py"),
            ("Trust",        "pages/3_Trust.py"),
            ("Groups",       "pages/4_Groups.py"),
            ("Analytics",    "pages/6_Analytics.py"),
            ("Profile",      "pages/5_Profile.py"),
        ]

        for label, path in pages:
            is_active = label == active
            if is_active:
                st.markdown('<div class="nav-active">', unsafe_allow_html=True)
            if st.button(f"  {label}", key=f"nav_{label}"):
                st.switch_page(path)
            if is_active:
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div style="border-top:1px solid {BORDER};margin:0.5rem 1rem;"></div>
        <div style="font-size:10px;color:{TEXT_MUTED};text-transform:uppercase;
                    letter-spacing:0.08em;padding:0 1.2rem 4px;">
          Quick Actions
        </div>
        """, unsafe_allow_html=True)

        if st.button("＋  New Transaction", key="nav_new_tx"):
            st.switch_page("pages/2_Transactions.py")

        st.markdown(
            f'<div style="border-top:1px solid {BORDER};margin:0.5rem 1rem 0.25rem;"></div>',
            unsafe_allow_html=True
        )

        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button(" Log out", key="nav_logout"):
            st.session_state.clear()
            st.switch_page("app.py")
        st.markdown('</div>', unsafe_allow_html=True)


# ── UI helpers ────────────────────────────────────────────────

def stat_card(label, value, sub="", accent=False):
    cls = "pl-stat accent" if accent else "pl-stat"
    sub_html = f'<div class="stat-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="{cls}">
        <div class="stat-label">{label}</div>
        <div class="stat-value">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def trust_badge(score: float) -> str:
    s = round(score)
    if score >= 70:   return f'<span class="trust-high">↑ {s}</span>'
    elif score >= 40: return f'<span class="trust-mid">◆ {s}</span>'
    else:             return f'<span class="trust-low">↓ {s}</span>'


def status_badge(status: str) -> str:
    label = status.replace("_", " ").capitalize()
    return f'<span class="badge badge-{status}">{label}</span>'


def trust_color(score: float) -> str:
    if score >= 70:   return SUCCESS
    elif score >= 40: return GOLD
    else:             return DANGER


def trust_ring_svg(score: float, size: int = 120) -> str:
    stroke = 8
    r      = (size - stroke) / 2
    circ   = 2 * 3.14159 * r
    offset = circ - (score / 100) * circ
    color  = trust_color(score)
    label  = "Excellent" if score >= 70 else "Good" if score >= 50 else "Fair" if score >= 25 else "Poor"
    return f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:8px;">
      <div style="position:relative;width:{size}px;height:{size}px;">
        <svg width="{size}" height="{size}" style="transform:rotate(-90deg);">
          <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none"
            stroke="{BORDER}" stroke-width="{stroke}"/>
          <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none"
            stroke="{color}" stroke-width="{stroke}"
            stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}"
            stroke-linecap="round"/>
        </svg>
        <div style="position:absolute;inset:0;display:flex;flex-direction:column;
                    align-items:center;justify-content:center;">
          <span style="font-size:24px;font-weight:500;color:{color};
                       font-family:'DM Serif Display',Georgia,serif;line-height:1;">
            {score:.0f}
          </span>
          <span style="font-size:11px;color:{TEXT_MUTED};margin-top:2px;">/100</span>
        </div>
      </div>
      <span style="font-size:13px;font-weight:500;color:{color};">{label}</span>
    </div>
    """


def fmt(amount) -> str:
    amount = float(amount or 0)
    return f"KES {int(amount):,}" if amount == int(amount) else f"KES {amount:,.2f}"


def page_title(title: str, subtitle: str = ""):
    sub_html = f'<p class="pl-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(f'<h1 class="pl-title">{title}</h1>{sub_html}', unsafe_allow_html=True)


def divider():
    st.markdown('<hr class="pl-divider">', unsafe_allow_html=True)