from pathlib import Path
import yaml

from yaml.loader import SafeLoader
from streamlit_authenticator.utilities.hasher import Hasher


AUTH_CONFIG_PATH = Path("src/frontend/auth/auth_config.yaml")


def register_user(
    username: str,
    name: str,
    email: str,
    password: str,
):
    """
    Registers a new user in auth_config.yaml.
    """

    with open(AUTH_CONFIG_PATH, "r", encoding="utf-8") as file:
        config = yaml.load(file, Loader=SafeLoader)

    if username in config["credentials"]["usernames"]:
        raise ValueError("Username already exists.")

    hashed_password = Hasher.hash(password)

    config["credentials"]["usernames"][username] = {
        "email": email,
        "name": name,
        "password": hashed_password,
    }

    with open(AUTH_CONFIG_PATH, "w", encoding="utf-8") as file:
        yaml.dump(
            config,
            file,
            default_flow_style=False,
            sort_keys=False,
        )

    user_dir = Path("data/users") / username

    (user_dir / "uploads").mkdir(parents=True, exist_ok=True)
    (user_dir / "chroma").mkdir(parents=True, exist_ok=True)

    return True