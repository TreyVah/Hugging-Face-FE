"""
Streamlit entry point.
Handles session state, login/register UI, and page navigation.
"""
import streamlit as st
from frontend.components import api_client as api
from frontend.components.cards import inject_global_css
from frontend.views import score, dashboard, history, batch, ab_dashboard, admin

st.set_page_config(
    page_title="RiskNova",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

st.markdown("""
<style>
    section[data-testid="stSidebar"] { padding-top: 1rem; }
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Session state initialisation
if "token"    not in st.session_state: st.session_state.token    = None
if "username" not in st.session_state: st.session_state.username = None
if "role"     not in st.session_state: st.session_state.role     = "analyst"
if "page"     not in st.session_state: st.session_state.page     = "Score Applicant"


# ─────────────────────────────────────────────
# Auth UI
# ─────────────────────────────────────────────
def show_auth():
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:32px 0 24px">
            <div style="font-size:52px"></div>
            <h1 style="font-size:26px;font-weight:700;margin:8px 0 4px">
                RiskNova</h1>
            <p style="color:#888;font-size:15px">
                AI-powered loan decision support</p>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["Login", "Create account"])

        with tab_login:
            with st.form("login_form"):
                username  = st.text_input("Username")
                password  = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please enter username and password.")
                else:
                    try:
                        token = api.login(username, password)
                        st.session_state.token    = token
                        st.session_state.username = username

                        # Decode role from JWT token
                        from jose import jwt as jose_jwt
                        payload = jose_jwt.decode(
    token,
    key="",
    algorithms=["HS256"],
    options={"verify_signature": False}
)
                        st.session_state.role = payload.get("role", "analyst")
                        st.rerun()
                    except RuntimeError as e:
                        st.error(str(e))

        with tab_register:
            with st.form("register_form"):
                new_user  = st.text_input("Username",               key="reg_user")
                new_email = st.text_input("Email",                  key="reg_email")
                new_pass  = st.text_input("Password (min 8 chars)", key="reg_pass",
                                          type="password")
                submitted = st.form_submit_button("Create account",
                                                   use_container_width=True)
            if submitted:
                try:
                    api.register(new_user, new_email, new_pass)
                    st.success("Account created! Please log in.")
                except RuntimeError as e:
                    st.error(str(e))

        st.markdown("<br>", unsafe_allow_html=True)
        healthy = api.health_check()
        if healthy:
            st.success(" API is online")
        else:
            st.error(" Cannot reach API — is the backend running?")


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
def show_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:8px 0 20px">
            <div style="font-size:36px"></div>
            <div style="font-weight:700;font-size:17px">Credit Risk System</div>
        </div>
        """, unsafe_allow_html=True)

        role = st.session_state.get("role", "analyst")

        # Pages for all users
        pages = {
            "Score Applicant": "",
            "Batch Upload":    "",
            "Dashboard":       "",
            "History":         "",
        }

        # Admin-only pages
        if role == "admin":
            pages["A/B Testing"] = ""
            pages["Admin Panel"] = ""

        for page_name, icon in pages.items():
            active    = st.session_state.page == page_name
            btn_style = "primary" if active else "secondary"
            if st.button(
                f"{icon}  {page_name}",
                key=f"nav_{page_name}",
                use_container_width=True,
                type=btn_style,
            ):
                st.session_state.page = page_name
                st.rerun()

        st.markdown("---")

        healthy    = api.health_check()
        status_dot = "" if healthy else ""
        st.caption(f"{status_dot} API {'online' if healthy else 'offline'}")

        role_icon = "" if role == "admin" else ""
        st.caption(f"{role_icon} **{st.session_state.username}** ({role})")

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()


# ─────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────
def main():
    if not st.session_state.token:
        show_auth()
        return

    show_sidebar()

    page = st.session_state.page
    role = st.session_state.get("role", "analyst")

    if page == "Score Applicant":
        score.render()
    elif page == "Batch Upload":
        batch.render()
    elif page == "Dashboard":
        dashboard.render()
    elif page == "History":
        history.render()
    elif page == "A/B Testing":
        if role != "admin":
            st.error(" Admin access required.")
        else:
            ab_dashboard.render()
    elif page == "Admin Panel":
        if role != "admin":
            st.error(" Admin access required.")
        else:
            admin.render()


if __name__ == "__main__":
    main()