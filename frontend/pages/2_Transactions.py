import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from config import (
    page_setup, require_auth, page_title, divider, sidebar_nav,
    status_badge, fmt,
    GOLD, BG_SURFACE, BG_RAISED, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    SUCCESS, DANGER, WARNING, INFO,
)
import api

page_setup("NitaRefund · Transactions")
require_auth()
sidebar_nav("Transactions")
if "form_version" not in st.session_state:
    st.session_state.form_version = 0
# Persist active tab across reruns
if "tx_tab" not in st.session_state:
    st.session_state.tx_tab = 0

username = st.session_state.get("username", "User")


@st.cache_data(ttl=20, show_spinner=False)
def load_transactions(token):
    try:    return api.get_my_transactions(limit=50)
    except: return []

txns = load_transactions(st.session_state.token)

page_title("Transactions", "Log, approve, and settle peer transactions.")
divider()


# ── Helper ────────────────────────────────────────────────────
def fmt_date(iso):
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return str(iso)[:10]


def action_button(label, action, tx_id, style="primary"):
    if style == "danger":
        st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
    elif style == "ghost":
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)

    if st.button(label, key=f"btn_{action}_{tx_id}"):
        try:
            api.transaction_action(tx_id, action)
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            try:
                msg = e.response.json() if hasattr(e, "response") and e.response else {}
            except Exception:
                msg = {}
            st.error(msg.get("detail", "Action failed — check the server logs."))

    if style in ("danger", "ghost"):
        st.markdown('</div>', unsafe_allow_html=True)


# NEW — count badges on the tab labels
pending_count  = sum(1 for t in txns
                     if t["status"] == "pending"
                     and t["borrower_username"] == username)
awaiting_count = sum(1 for t in txns
                     if t["status"] == "awaiting_confirmation"
                     and t["lender_username"] == username)
action_count   = pending_count + awaiting_count

pending_label = (
    f"Pending Actions  🔴" if action_count > 0 else "Pending Actions"
)

all_tab, new_tab, pending_tab = st.tabs([
    f"All Transactions",
    "New Transaction",
    pending_label,
])


# ═══════════════════════════════════════════════════
# TAB 1 — All Transactions
# ═══════════════════════════════════════════════════
with all_tab:

    # Filters row
    fc1, fc2, fc3, fc4, fc5 = st.columns([3, 2, 2, 2, 2])
    with fc1:
        search = st.text_input("Search", placeholder="Search by description",
                               key="f_search", label_visibility="collapsed")
    with fc2:
        status_f = st.selectbox("Status", ["All", "Pending", "Approved",
            "Awaiting", "Settled", "Rejected", "Cancelled", "Disputed"],
            key="f_status", label_visibility="collapsed")
    with fc3:
        type_f = st.selectbox("Type", ["All", "Monetary", "Service"],
                              key="f_type", label_visibility="collapsed")
    with fc4:
        dir_f = st.selectbox("Direction", ["All", "Lent", "Borrowed"],
                             key="f_dir", label_visibility="collapsed")
    with fc5:
        tx_id_f = st.text_input("TX ID", placeholder="e.g. 42",
                                key="f_txid", label_visibility="collapsed")

    # Apply filters
    filtered = txns

    if search:
        filtered = [t for t in filtered
                    if search.lower() in (t.get("description") or "").lower()]
    if status_f != "All":
        smap = {
            "Pending": "pending", "Approved": "approved",
            "Awaiting": "awaiting_confirmation", "Settled": "settled",
            "Rejected": "rejected", "Cancelled": "cancelled",
            "Disputed": "disputed"
        }
        filtered = [t for t in filtered if t["status"] == smap[status_f]]
    if type_f != "All":
        filtered = [t for t in filtered
                    if t.get("transaction_type","").lower() == type_f.lower()]
    if dir_f == "Lent":
        filtered = [t for t in filtered if t["lender_username"] == username]
    elif dir_f == "Borrowed":
        filtered = [t for t in filtered if t["borrower_username"] == username]
    if tx_id_f.strip():
        try:
            tid = int(tx_id_f.strip())
            filtered = [t for t in filtered if t["id"] == tid]
        except ValueError:
            pass

    # Results count
    st.markdown(
        f'<div style="background:{BG_RAISED};border:1px solid {BORDER};'
        f'border-radius:10px;padding:10px 16px;margin:1rem 0;'
        f'font-size:13px;font-weight:500;color:{TEXT_MUTED};">'
        f'{len(filtered)} RESULT{"S" if len(filtered) != 1 else ""}'
        f'</div>',
        unsafe_allow_html=True
    )

    if not filtered:
        st.markdown(
            f'<p style="color:{TEXT_MUTED};font-size:14px;'
            f'text-align:center;padding:2rem 0;">No transactions match this filter.</p>',
            unsafe_allow_html=True
        )
    else:
        for tx in filtered:
            is_lender    = tx["lender_username"] == username
            counterparty = tx["borrower_username"] if is_lender else tx["lender_username"]
            counter_id   = tx["borrower_id"] if is_lender else tx["lender_id"]
            direction    = "Lent to" if is_lender else "Borrowed from"
            dir_color    = SUCCESS if is_lender else WARNING
            amount_sign  = f"+{fmt(tx['amount'])}" if is_lender else f"−{fmt(tx['amount'])}"
            status       = tx["status"]
            tx_type      = tx.get("transaction_type", "monetary")
            date_str     = fmt_date(tx.get("created_at", ""))

            # Title: description or auto-name
            title = tx.get("description") or f"Transaction #{tx['id']}"

            # Subtitle line
            subtitle_parts = [
                f"{direction} User {counter_id}",
                f"ID:{counter_id}",
                f"TX#{tx['id']}",
                tx_type,
                date_str,
            ]
            subtitle_line = " · ".join(subtitle_parts)

            st.markdown(f"""
            <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                        border-radius:12px;padding:14px 18px;margin-bottom:8px;">
              <div style="display:flex;align-items:flex-start;
                          justify-content:space-between;gap:12px;flex-wrap:wrap;">
                <div style="flex:1;min-width:180px;">
                  <div style="font-size:14px;font-weight:500;
                              color:{TEXT_PRIMARY};margin-bottom:3px;">
                    {title}
                  </div>
                  <div style="font-size:11px;color:{TEXT_MUTED};">
                    {subtitle_line}
                  </div>
                </div>
                <div style="text-align:right;flex-shrink:0;">
                  <div style="font-size:15px;font-weight:500;color:{dir_color};
                              font-family:'DM Serif Display',Georgia,serif;">
                    {amount_sign}
                  </div>
                  <div style="margin-top:5px;">{status_badge(status)}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# TAB 2 — New Transaction
# ═══════════════════════════════════════════════════
with new_tab:
    st.markdown(f"""
    <div style="font-family:'DM Serif Display',Georgia,serif;
                font-size:20px;color:{TEXT_PRIMARY};margin:1rem 0 4px;">
      Create Transaction
    </div>
    <div style="font-size:13px;color:{TEXT_MUTED};margin-bottom:1.5rem;">
      You are the lender. Enter the borrower's User ID.
    </div>
    """, unsafe_allow_html=True)

    # form_version changes key names → widgets reset after submission
    v = st.session_state.form_version

    na, nb = st.columns(2)
    with na:
        borrower_id = st.number_input(
            "Borrower User ID",
            min_value=1, step=1, value=1,
            key=f"nt_borrower_{v}"
        )
        amount = st.number_input(
            "Amount (KES)",
            min_value=1, step=100, value=1000,
            format="%d",
            key=f"nt_amount_{v}"
        )
    with nb:
        tx_type  = st.selectbox("Type", ["monetary", "service"],
                                key=f"nt_type_{v}")
        due_date = st.date_input("Due Date (optional)", value=None,
                                 key=f"nt_due_{v}")

    description = st.text_input(
        "Description (optional)",
        key=f"nt_desc_{v}",
        placeholder="e.g. lunch money, rent split, fare"
    )

    if st.button("Create Transaction", key=f"btn_create_{v}"):
        try:
            api.create_transaction(
                borrower_id=int(borrower_id),
                amount=float(amount),
                tx_type=tx_type,
                description=description,
                due_date=due_date if due_date else None,
            )
            st.success(f"✓ Transaction created for {fmt(float(amount))}. The borrower needs to approve it.")
            st.session_state.form_version += 1   # resets all form fields
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            msg = getattr(getattr(e, "response", None), "json", lambda: {})()
            st.error(msg.get("detail", "Could not create transaction."))

# ═══════════════════════════════════════════════════
# TAB 3 — Pending Actions
# ═══════════════════════════════════════════════════
with pending_tab:

    # As lender: awaiting_confirmation = borrower has paid, I need to confirm
    # As borrower: pending = needs my approval; approved = I need to pay

    lender_awaiting = [
        t for t in txns
        if t["lender_username"] == username
        and t["status"] == "awaiting_confirmation"
    ]
    borrower_pending = [
        t for t in txns
        if t["borrower_username"] == username
        and t["status"] == "pending"
    ]
    borrower_approved = [
        t for t in txns
        if t["borrower_username"] == username
        and t["status"] == "approved"
    ]

    all_pending = lender_awaiting + borrower_pending + borrower_approved

    if not all_pending:
        st.markdown(f"""
        <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                    border-radius:14px;padding:3rem 2rem;text-align:center;
                    margin-top:1rem;">
          <div style="font-size:36px;margin-bottom:12px;">✅</div>
          <div style="font-size:15px;font-weight:500;
                      color:{TEXT_PRIMARY};margin-bottom:6px;">
            All clear
          </div>
          <div style="font-size:13px;color:{TEXT_MUTED};">
            No transactions need your attention right now.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for tx in all_pending:
            is_lender    = tx["lender_username"] == username
            counterparty = tx["borrower_username"] if is_lender else tx["lender_username"]
            status       = tx["status"]
            title        = tx.get("description") or f"Transaction #{tx['id']}"

            # Context label
            if is_lender and status == "awaiting_confirmation":
                context = f"Owed to you from {counterparty}"
                note    = "⏳ Borrower has marked this as settled.  Confirm if received, or reject to send back for retry."
                note_color = WARNING
            elif not is_lender and status == "pending":
                context = f"Requested by {counterparty}"
                note    = "📋 This transaction needs your approval."
                note_color = INFO
            else:
                context = f"Approved — pay {counterparty} to settle"
                note    = "💸 You have approved this. Mark as paid when you've transferred."
                note_color = GOLD

            st.markdown(f"""
            <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                        border-radius:14px;padding:16px 20px;margin-bottom:12px;">
              <div style="font-size:11px;color:{TEXT_MUTED};margin-bottom:6px;">
                {context}
              </div>
              <div style="display:flex;justify-content:space-between;
                          align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:10px;">
                <div>
                  <div style="font-size:15px;font-weight:500;color:{TEXT_PRIMARY};">
                    {title}
                  </div>
                  <div style="font-size:12px;color:{TEXT_MUTED};margin-top:2px;">
                    TX #{tx['id']}
                  </div>
                </div>
                <div style="text-align:right;">
                  <div style="font-size:16px;font-weight:500;color:{GOLD};
                              font-family:'DM Serif Display',Georgia,serif;">
                    {fmt(tx['amount'])}
                  </div>
                  <div style="margin-top:4px;">{status_badge(status)}</div>
                </div>
              </div>
              <div style="font-size:12px;color:{note_color};
                          background:rgba(255,255,255,0.03);border-radius:8px;
                          padding:8px 12px;margin-bottom:12px;">
                {note}
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons
            if is_lender and status == "awaiting_confirmation":
                b1, b2, _ = st.columns([2, 2, 3])
                with b1: action_button(f"✅ Confirm Receipt #{tx['id']}", "confirm", tx["id"])
                with b2: action_button(f"✗ Reject #{tx['id']}", "reject", tx["id"], style="danger")

            elif not is_lender and status == "pending":
                b1, b2, _ = st.columns([2, 2, 3])
                with b1: action_button(f"✓ Approve", "approve", tx["id"])
                with b2: action_button(f"✗ Decline", "dispute", tx["id"], style="danger")

            elif not is_lender and status == "approved":
                b1, _ = st.columns([3, 3])
                with b1: action_button(f"💸 Mark as Paid", "pay", tx["id"])