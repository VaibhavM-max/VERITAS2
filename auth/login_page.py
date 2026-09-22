"""Streamlit login view for OTP-based dashboard access."""

import streamlit as st

from auth.otp_auth import auth_manager


def render_login_page() -> None:
    """Render the email and OTP steps without exposing OTP values in the UI."""
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">Protected operations</div>
          <h1>Sign in to VERITAS</h1>
          <p>Verify your email to open the evidence control room.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.setdefault("login_step", "email")
    st.session_state.setdefault("login_email", "")

    if st.session_state.login_step == "email":
        with st.form("request_otp"):
            email = st.text_input("Work email", placeholder="you@example.com")
            submitted = st.form_submit_button("Send one-time code", type="primary")
        if submitted:
            success, message = auth_manager.request_otp(email)
            if success:
                st.session_state.login_email = email.strip().lower()
                st.session_state.login_step = "otp"
                st.rerun()
            st.error(message)
        st.caption("Demo mode prints the code to the server console when SMTP is not configured.")
        return

    st.info(f"A code was sent to {st.session_state.login_email}.")
    with st.form("verify_otp"):
        otp = st.text_input("One-time code", max_chars=6, type="password", placeholder="6 digits")
        columns = st.columns(2)
        verify = columns[0].form_submit_button("Verify code", type="primary", use_container_width=True)
        resend = columns[1].form_submit_button("Send again", use_container_width=True)

    if resend:
        success, message = auth_manager.request_otp(st.session_state.login_email)
        (st.success if success else st.error)(message)
    if verify:
        success, message, session_id = auth_manager.verify_otp(st.session_state.login_email, otp)
        if success and session_id:
            st.session_state.logged_in = True
            st.session_state.session_id = session_id
            st.session_state.user_email = st.session_state.login_email
            st.session_state.login_step = "email"
            st.rerun()
        st.error(message)
    if st.button("Use a different email"):
        st.session_state.login_step = "email"
        st.session_state.login_email = ""
        st.rerun()