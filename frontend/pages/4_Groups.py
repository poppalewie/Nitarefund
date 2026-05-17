import streamlit as st
from datetime import datetime
from config import (
    page_setup, require_auth, page_title, divider, sidebar_nav,
    status_badge, fmt,
    GOLD, BG_SURFACE, BG_RAISED, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    SUCCESS, WARNING, INFO,
)
import api

page_setup("NitaRefund · Groups")
require_auth()
sidebar_nav("Groups")

if "grp_form_version" not in st.session_state:
    st.session_state.grp_form_version = 0

username = st.session_state.get("username", "User")


@st.cache_data(ttl=20, show_spinner=False)
def load_groups(token):
    try:    return api.get_my_groups()
    except: return []

groups = load_groups(st.session_state.token)

page_title("Groups", "Split bills equally across multiple peers.")
divider()

create_tab, history_tab = st.tabs(["New Split", "My Groups"])

# ═══════════════════════════════════════════════════
# TAB 1 — Create
# ═══════════════════════════════════════════════════
with create_tab:
    v = st.session_state.grp_form_version

    ga, gb = st.columns(2)
    with ga:
        user_ids_input = st.text_input(
            "Peer User IDs (comma separated)",
            key=f"grp_ids_{v}", placeholder="e.g. 2, 5, 8"
        )
        description = st.text_input(
            "Description", key=f"grp_desc_{v}",
            placeholder="e.g. Dinner at Java, Uber split"
        )
    with gb:
        total_amount = st.number_input(
            "Total Amount (KES)", min_value=1,
            step=100, value=1000, format="%d",
            key=f"grp_amount_{v}"
        )

        # Live split preview
        if user_ids_input.strip() and total_amount:
            try:
                ids = [int(x.strip()) for x in user_ids_input.split(",")
                       if x.strip()]
                if ids:
                    total_ppl  = len(ids) + 1   # peers + you
                    per_person = total_amount / total_ppl
                    st.markdown(f"""
                    <div style="background:rgba(233,196,106,0.06);
                                border:1px solid rgba(233,196,106,0.20);
                                border-radius:10px;padding:14px 16px;margin-top:4px;">
                      <div style="font-size:11px;color:{TEXT_MUTED};
                                  text-transform:uppercase;letter-spacing:0.06em;
                                  margin-bottom:4px;">Split Preview</div>
                      <div style="font-size:22px;
                                  font-family:'DM Serif Display',Georgia,serif;
                                  color:{GOLD};">
                        {fmt(per_person)} each
                      </div>
                      <div style="font-size:12px;color:{TEXT_MUTED};margin-top:3px;">
                        {total_ppl} people · {fmt(total_amount)} total
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
            except ValueError:
                pass

    if st.button("Create Group Split", key=f"btn_create_group_{v}"):
        try:
            ids = [int(x.strip()) for x in user_ids_input.split(",") if x.strip()]
            if not ids:
                st.error("Enter at least one peer User ID.")
            else:
                result = api.create_group(
                    user_ids=ids,
                    total_amount=float(total_amount),
                    description=description,
                )
                total_ppl = len(ids) + 1
                st.success(
                    f"✓ Group split created — "
                    f"{fmt(float(total_amount) / total_ppl)} each across {total_ppl} people."
                )
                st.session_state.grp_form_version += 1
                st.cache_data.clear()
                st.rerun()
        except ValueError:
            st.error("User IDs must be numbers separated by commas.")
        except Exception as e:
            try:
                msg = e.response.json() if hasattr(e, "response") and e.response else {}
            except Exception:
                msg = {}
            st.error(msg.get("detail", "Could not create group split."))

# ═══════════════════════════════════════════════════
# TAB 2 — History
# ═══════════════════════════════════════════════════
with history_tab:
    if not groups:
        st.markdown(f"""
        <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                    border-radius:14px;padding:3rem 2rem;text-align:center;
                    margin-top:1rem;">
          <div style="font-size:36px;margin-bottom:12px;">👥</div>
          <div style="font-size:15px;font-weight:500;
                      color:{TEXT_PRIMARY};margin-bottom:6px;">
            No group splits yet
          </div>
          <div style="font-size:13px;color:{TEXT_MUTED};">
            Create your first split in the New Split tab.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="font-size:13px;color:{TEXT_MUTED};'
            f'margin-bottom:12px;">'
            f'{len(groups)} group{"s" if len(groups) != 1 else ""}</div>',
            unsafe_allow_html=True
        )

        for g in groups:
            try:
                dt       = datetime.fromisoformat(g["created_at"].replace("Z", "+00:00"))
                date_str = dt.strftime("%-d %b %Y")
            except Exception:
                date_str = ""

            role = "Organiser" if g["is_creator"] else "Member"
            role_color = GOLD if g["is_creator"] else INFO

            settled = g["settled_count"]
            pending = g["pending_count"]
            total_m = g["member_count"]

            # Progress bar width
            progress = int((settled / (total_m - 1) * 100)) if total_m > 1 else 0

            members_html = " ".join(
                f'<span style="display:inline-flex;align-items:center;'
                f'justify-content:center;width:26px;height:26px;border-radius:50%;'
                f'background:{BG_RAISED};border:1px solid {BORDER};'
                f'font-size:10px;color:{TEXT_MUTED};font-weight:600;">'
                f'{m["username"][0].upper()}</span>'
                for m in g["members"]
            )

            st.markdown(f"""
            <div style="background:{BG_SURFACE};border:1px solid {BORDER};
                        border-radius:14px;padding:18px 20px;margin-bottom:10px;">

              <div style="display:flex;justify-content:space-between;
                          align-items:flex-start;flex-wrap:wrap;gap:8px;
                          margin-bottom:12px;">
                <div>
                  <div style="font-size:15px;font-weight:500;color:{TEXT_PRIMARY};
                              margin-bottom:3px;">
                    {g['description'] or f"Group #{g['id']}"}
                  </div>
                  <div style="font-size:11px;color:{TEXT_MUTED};">
                    Group #{g['id']} · {date_str} ·
                    <span style="color:{role_color};">{role}</span>
                  </div>
                </div>
                <div style="text-align:right;">
                  <div style="font-family:'DM Serif Display',Georgia,serif;
                              font-size:20px;color:{GOLD};line-height:1;">
                    {fmt(g['total_amount'])}
                  </div>
                  <div style="font-size:12px;color:{TEXT_MUTED};margin-top:2px;">
                    {fmt(g['share'])} per person · {total_m} people
                  </div>
                </div>
              </div>

              <!-- Members avatars -->
              <div style="display:flex;gap:4px;margin-bottom:12px;">
                {members_html}
              </div>

              <!-- Settlement progress -->
              <div style="margin-bottom:4px;">
                <div style="display:flex;justify-content:space-between;
                            font-size:11px;color:{TEXT_MUTED};margin-bottom:5px;">
                  <span>Settlement progress</span>
                  <span>{settled} / {total_m - 1} settled</span>
                </div>
                <div style="background:{BG_RAISED};border-radius:9999px;
                            height:4px;overflow:hidden;">
                  <div style="width:{progress}%;height:100%;
                              background:{SUCCESS if progress == 100 else GOLD};
                              border-radius:9999px;"></div>
                </div>
              </div>

              {f'<div style="font-size:12px;color:{WARNING};margin-top:6px;">⏳ {pending} pending</div>' if pending else ''}
              {f'<div style="font-size:12px;color:{SUCCESS};margin-top:6px;">✓ Fully settled</div>' if progress == 100 else ''}

            </div>
            """, unsafe_allow_html=True)