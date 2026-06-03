import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


DEFAULT_USER_ID = "default_user"
BASE_DATA_DIR = Path("data/users")


def get_user_quiz_history_path(user_id: str = DEFAULT_USER_ID) -> Path:
    """
    Returns the quiz history JSON file path for a user.

    Creates the parent user directory if it does not already exist.
    """
    user_dir = BASE_DATA_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "quiz_attempts.json"


def load_quiz_attempts(user_id: str = DEFAULT_USER_ID) -> list[dict]:
    """
    Loads all saved quiz attempts for a user.

    Returns an empty list if the history file does not exist yet.
    """
    history_path = get_user_quiz_history_path(user_id)

    if not history_path.exists():
        return []

    with open(history_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_quiz_attempt(attempt_data: dict, user_id: str = DEFAULT_USER_ID) -> dict:
    """
    Saves a completed quiz attempt to the user's quiz history file.

    Adds metadata such as quiz_id and created_at before persisting.
    """
    attempts = load_quiz_attempts(user_id)

    saved_attempt = {
        "quiz_id": str(uuid4()),
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
        **attempt_data,
    }

    attempts.append(saved_attempt)

    history_path = get_user_quiz_history_path(user_id)

    with open(history_path, "w", encoding="utf-8") as file:
        json.dump(attempts, file, indent=2)

    return saved_attempt


def get_quiz_summary(user_id: str = DEFAULT_USER_ID) -> dict:
    """
    Calculates dashboard-friendly quiz metrics for a user.

    Metrics include:
    - total attempts
    - average score percentage
    - best score percentage
    - recent attempts
    """
    attempts = load_quiz_attempts(user_id)

    if not attempts:
        return {
            "total_attempts": 0,
            "average_score_percentage": 0,
            "best_score_percentage": 0,
            "recent_attempts": [],
        }

    percentages = [
        attempt.get("percentage", 0)
        for attempt in attempts
    ]

    recent_attempts = list(reversed(attempts[-5:]))

    return {
        "total_attempts": len(attempts),
        "average_score_percentage": round(sum(percentages) / len(percentages), 2),
        "best_score_percentage": max(percentages),
        "recent_attempts": recent_attempts,
    }