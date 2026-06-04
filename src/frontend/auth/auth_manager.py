from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


AUTH_CONFIG_PATH = Path("src/frontend/auth/auth_config.yaml")


def load_auth_config() -> dict:
    """
    Loads Streamlit authentication configuration from YAML.

    Returns:
        dict: Authentication configuration containing users, cookie settings,
        and preauthorized emails.
    """
    with open(AUTH_CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.load(file, Loader=SafeLoader)


def get_authenticator():
    """
    Creates and returns a Streamlit Authenticator instance.

    Returns:
        Authenticate: Streamlit Authenticator object used for login/logout.
    """
    config = load_auth_config()

    return stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )


def require_login() -> str:
    """
    Protects a Streamlit page and returns the logged-in username.

    Returns:
        str: Logged-in username.

    Stops:
        Streamlit execution if the user is not authenticated.
    """
    authenticator = get_authenticator()

    authenticator.login(location="main")

    authentication_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")
    name = st.session_state.get("name")

    if authentication_status is False:
        st.error("Username or password is incorrect.")
        st.stop()

    if authentication_status is None:
        st.warning("Please enter your username and password.")
        st.stop()

    st.sidebar.success(f"Logged in as {name}")
    authenticator.logout("Logout", "sidebar")

    return username


def get_logged_in_user_id() -> str:
    """
    Returns the current logged-in username from Streamlit session state.

    Returns:
        str: Logged-in username.
    """
    return st.session_state.get("username", "default_user")