import streamlit as st

# Reset auth flags in session state
st.session_state["authenticated"] = False
st.session_state["user"] = None
st.session_state["auth_mode"] = "login"

st.info("Logging out...")
st.rerun()
