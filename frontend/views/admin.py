"""
Admin Panel — user management UI.
Only visible to users with role='admin'.
"""
import streamlit as st
import requests
import os

from frontend.components.cards import section_header, metric_card

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

ROLE_COLOURS = {
    "admin":   "#EF9F27",
    "analyst": "#3B8BD4",
}


def _headers():
    return {"Authorization": f"Bearer {st.session_state.get('token', '')}"}


def _get(endpoint):
    r = requests.get(f"{API_BASE}{endpoint}", headers=_headers(), timeout=15)
    if r.status_code == 403:
        raise PermissionError("Admin access required.")
    if not r.ok:
        raise RuntimeError(f"API error {r.status_code}: {r.json().get('detail')}")
    return r.json()


def _post(endpoint, json=None, params=None):
    r = requests.post(
        f"{API_BASE}{endpoint}",
        headers=_headers(),
        json=json,
        params=params,
        timeout=15,
    )
    if r.status_code == 403:
        raise PermissionError("Admin access required.")
    if not r.ok:
        raise RuntimeError(f"API error {r.status_code}: {r.json().get('detail')}")
    return r.json()


def _put(endpoint, json=None):
    r = requests.put(
        f"{API_BASE}{endpoint}",
        headers=_headers(),
        json=json,
        timeout=15,
    )
    if not r.ok:
        raise RuntimeError(f"API error {r.status_code}: {r.json().get('detail')}")
    return r.json()


def _delete(endpoint):
    r = requests.delete(f"{API_BASE}{endpoint}", headers=_headers(), timeout=15)
    if not r.ok:
        raise RuntimeError(f"API error {r.status_code}: {r.json().get('detail')}")
    return r.json()

def render():
    st.title(" Admin Panel")
    st.caption("User management — Admin access only.")

    # ── Permission check on frontend side too
    role = st.session_state.get("role", "analyst")
    if role != "admin":
        st.error(" You do not have permission to view this page.")
        st.info("Contact your system administrator to request admin access.")
        return

    # ─────────────────────────────────────────
    # Load users
    # ─────────────────────────────────────────
    try:
        data  = _get("/users")
        users = data["users"]
    except PermissionError as e:
        st.error(str(e))
        return
    except RuntimeError as e:
        st.error(str(e))
        return

    # ─────────────────────────────────────────
    # KPI cards
    # ─────────────────────────────────────────
    section_header("User Overview")
    total    = data["total"]
    admins   = sum(1 for u in users if u["role"] == "admin")
    analysts = sum(1 for u in users if u["role"] == "analyst")
    active   = sum(1 for u in users if u["is_active"])

    k1, k2, k3, k4 = st.columns(4)
    with k1: metric_card("Total Users",  str(total),    colour="#3B8BD4")
    with k2: metric_card("Admins",       str(admins),   colour="#EF9F27")
    with k3: metric_card("Analysts",     str(analysts), colour="#1D9E75")
    with k4: metric_card("Active",       str(active),   colour="#1D9E75")

    # ─────────────────────────────────────────
    # User table
    # ─────────────────────────────────────────
    st.markdown("---")
    section_header("All Users")

    for user in users:
        role_colour = ROLE_COLOURS.get(user["role"], "#888")
        status_icon = "" if user["is_active"] else ""
        role_icon   = "" if user["role"] == "admin" else ""

        with st.expander(
            f"{status_icon} {role_icon} **{user['username']}** "
            f"— {user['role'].title()} "
            f"{'(inactive)' if not user['is_active'] else ''}"
        ):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Email:** {user['email']}")
            c2.markdown(f"**Role:** `{user['role']}`")
            c3.markdown(
                f"**Status:** {'Active ' if user['is_active'] else 'Inactive '}"
            )
            c1.caption(f"ID: `{user['id'][:8]}...`")

            # Skip controls for current user
            if user["username"] == st.session_state.get("username"):
                st.caption("*(This is your account)*")
                continue

            action_col1, action_col2, action_col3 = st.columns(3)

            # Change role
            new_role = action_col1.selectbox(
                "Change role",
                ["analyst", "admin"],
                index=0 if user["role"] == "analyst" else 1,
                key=f"role_{user['id']}",
            )
            if action_col1.button(" Update role", key=f"update_{user['id']}"):
                try:
                    _put(f"/users/{user['id']}", json={"role": new_role})
                    st.success(f" {user['username']} is now {new_role}.")
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))

            # Toggle active
            toggle_label = " Deactivate" if user["is_active"] else " Activate"
            if action_col2.button(toggle_label, key=f"toggle_{user['id']}"):
                try:
                    if user["is_active"]:
                        _delete(f"/users/{user['id']}")
                        st.warning(f" {user['username']} deactivated.")
                    else:
                        _put(f"/users/{user['id']}", json={"is_active": True})
                        st.success(f" {user['username']} activated.")
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))

    # ─────────────────────────────────────────
    # Create new user
    # ─────────────────────────────────────────
    st.markdown("---")
    section_header("Create New User", "Admin-created users can have any role")

    with st.form("create_user_form"):
        f1, f2 = st.columns(2)
        new_username = f1.text_input("Username")
        new_email    = f2.text_input("Email")

        f3, f4 = st.columns(2)
        new_password = f3.text_input("Password (min 8 chars)", type="password")
        new_role     = f4.selectbox("Role", ["analyst", "admin"])

        submitted = st.form_submit_button(
            " Create user", type="primary", use_container_width=True
        )

    if submitted:
        if not all([new_username, new_email, new_password]):
            st.error("All fields are required.")
        else:
            try:
                _post("/users", json={
                    "username": new_username,
                    "email":    new_email,
                    "password": new_password,
                    "role":     new_role,
                })
                st.success(
                    f" User **{new_username}** created as **{new_role}**."
                )
                st.rerun()
            except RuntimeError as e:
                st.error(str(e))