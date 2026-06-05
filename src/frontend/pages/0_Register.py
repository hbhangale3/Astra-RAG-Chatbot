import re

import streamlit as st

from src.frontend.auth.register_user import register_user


st.title("👤 Register New User")

st.markdown(
    """
    Create a new Study Buddy AI account.
    """
)


def is_valid_email(email: str) -> bool:
    """
    Validates basic email format.
    """
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))


with st.form("register_form", clear_on_submit=True):
    username = st.text_input("Username")
    name = st.text_input("Full Name")
    email = st.text_input("Email")

    password = st.text_input(
        "Password",
        type="password",
    )

    confirm_password = st.text_input(
        "Confirm Password",
        type="password",
    )

    submitted = st.form_submit_button("Register")


if submitted:
    cleaned_username = username.strip().lower()
    cleaned_name = name.strip()
    cleaned_email = email.strip().lower()

    if not cleaned_username:
        st.error("Username is required.")

    elif " " in cleaned_username:
        st.error("Username cannot contain spaces.")

    elif not cleaned_name:
        st.error("Name is required.")

    elif not cleaned_email:
        st.error("Email is required.")

    elif not is_valid_email(cleaned_email):
        st.error("Please enter a valid email address.")

    elif password != confirm_password:
        st.error("Passwords do not match.")

    elif len(password) < 8:
        st.error("Password must contain at least 8 characters.")

    else:
        try:
            register_user(
                username=cleaned_username,
                name=cleaned_name,
                email=cleaned_email,
                password=password,
            )

            st.success(
                f"Account '{cleaned_username}' created successfully. "
                "You can now login."
            )

        except ValueError as e:
            st.error(str(e))

        except Exception as e:
            st.error(f"Registration failed: {e}")