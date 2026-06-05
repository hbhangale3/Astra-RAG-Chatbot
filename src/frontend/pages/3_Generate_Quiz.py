import requests
import streamlit as st

from src.frontend.config.frontend_config import Settings
from src.frontend.auth.auth_manager import require_login


settings = Settings()
username = require_login()

st.title("📝 Generate Quiz")

st.markdown(
    """
    Generate a source-grounded quiz from your uploaded study material.
    After generation, select your answers and submit the quiz to view your score.
    """
)

# User-specific Streamlit session keys.
generated_quiz_key = f"generated_quiz_{username}"
quiz_answers_key = f"quiz_answers_{username}"
quiz_submitted_key = f"quiz_submitted_{username}"

if generated_quiz_key not in st.session_state:
    st.session_state[generated_quiz_key] = None

if quiz_answers_key not in st.session_state:
    st.session_state[quiz_answers_key] = {}

if quiz_submitted_key not in st.session_state:
    st.session_state[quiz_submitted_key] = False


def save_quiz_attempt(
    topic: str,
    difficulty: str,
    question_type: str,
    score: int,
    total: int,
    percentage: float,
    questions: list,
):
    """
    Saves the completed quiz attempt to the backend for the logged-in user.
    """
    payload = {
        "topic": topic,
        "difficulty": difficulty,
        "question_type": question_type,
        "score": score,
        "total_questions": total,
        "percentage": percentage,
        "questions": questions,
        "user_id": username,
    }

    try:
        response = requests.post(
            settings.QUIZ_ATTEMPTS_URL,
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            st.success("Quiz attempt saved to history.")
        else:
            st.warning("Quiz was graded, but attempt could not be saved.")
            st.write(response.text)

    except requests.exceptions.RequestException as e:
        st.warning(f"Quiz was graded, but backend save failed: {e}")


def generate_quiz(
    topic: str,
    num_questions: int,
    difficulty: str,
    question_type: str,
):
    """
    Sends a quiz generation request to the backend.
    """
    payload = {
        "topic": topic,
        "num_questions": num_questions,
        "difficulty": difficulty,
        "question_type": question_type,
        "user_id": username,
    }

    try:
        response = requests.post(
            settings.QUIZ_GENERATE_URL,
            json=payload,
            timeout=300,
        )

        if response.status_code == 200:
            return response.json()

        st.error("Quiz generation failed.")
        st.write(response.json().get("detail", response.text))
        return None

    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend: {e}")
        return None


def render_quiz_questions(questions: list):
    """
    Renders quiz questions and stores selected answers for the logged-in user.
    """
    st.session_state[quiz_answers_key] = {}

    for index, question in enumerate(questions):
        question_number = index + 1

        st.subheader(f"Question {question_number}")
        st.write(question["question"])

        options = question["options"]

        selected_option = st.radio(
            label="Choose your answer:",
            options=list(options.keys()),
            format_func=lambda option_key: f"{option_key}. {options[option_key]}",
            key=f"{username}_question_{index}",
        )

        st.session_state[quiz_answers_key][index] = selected_option

        st.divider()


def grade_quiz(questions: list):
    """
    Grades the quiz and saves the attempt for the logged-in user.
    """
    score = 0
    total = len(questions)

    st.header("Quiz Results")

    for index, question in enumerate(questions):
        selected_answer = st.session_state[quiz_answers_key].get(index)
        correct_answer = question["correct_answer"]

        is_correct = selected_answer == correct_answer

        if is_correct:
            score += 1

        st.subheader(f"Question {index + 1}")
        st.write(question["question"])

        if is_correct:
            st.success(f"Correct. Your answer: {selected_answer}")
        else:
            st.error(
                f"Incorrect. Your answer: {selected_answer}. "
                f"Correct answer: {correct_answer}"
            )

        st.write(f"Explanation: {question['explanation']}")
        st.caption(f"Source: {question.get('source', 'unknown_source')}")

        st.divider()

    percentage = round((score / total) * 100, 2) if total else 0

    st.metric("Final Score", f"{score}/{total}")
    st.metric("Percentage", f"{percentage}%")

    save_quiz_attempt(
        topic=st.session_state[generated_quiz_key]["topic"],
        difficulty=st.session_state[generated_quiz_key]["difficulty"],
        question_type=st.session_state[generated_quiz_key]["question_type"],
        score=score,
        total=total,
        percentage=percentage,
        questions=questions,
    )

    st.session_state[quiz_submitted_key] = True


topic = st.text_input(
    "Topic",
    placeholder="Example: Java Collections, Spring Boot, Loop Instructions",
)

num_questions = st.number_input(
    "Number of questions",
    min_value=1,
    max_value=15,
    value=5,
)

difficulty = st.selectbox(
    "Difficulty",
    ["Easy", "Medium", "Hard"],
    index=1,
)

question_type = st.selectbox(
    "Question type",
    ["MCQ"],
)

if st.button("Generate Quiz"):
    if not topic.strip():
        st.warning("Please enter a topic.")
    else:
        with st.spinner("Generating source-grounded quiz..."):
            quiz_response = generate_quiz(
                topic=topic,
                num_questions=num_questions,
                difficulty=difficulty,
                question_type=question_type,
            )

            if quiz_response:
                st.session_state[generated_quiz_key] = quiz_response
                st.session_state[quiz_answers_key] = {}
                st.session_state[quiz_submitted_key] = False
                st.success("Quiz generated successfully.")

if st.session_state[generated_quiz_key]:
    quiz_data = st.session_state[generated_quiz_key]["quiz"]
    questions = quiz_data.get("questions", [])

    if not questions:
        st.warning("No quiz questions were generated.")
    else:
        render_quiz_questions(questions)

        if st.button("Submit Quiz"):
            grade_quiz(questions)