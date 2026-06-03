import streamlit as st

st.title("📝 Generate Quiz")

st.markdown(
    """
    Quiz generation will be connected in the next phase.

    Planned behavior:
    - Enter a topic
    - Select number of questions
    - Generate MCQs from uploaded notes
    - Mix easy, medium, and hard questions
    - Show answer key, explanation, and source documents
    """
)

topic = st.text_input("Topic", placeholder="Example: jump statements, loop instructions, CPU scheduling")
num_questions = st.number_input("Number of questions", min_value=1, max_value=30, value=10)
question_type = st.selectbox("Question type", ["MCQ", "Fill in the blank", "Mixed"])
difficulty_mode = st.selectbox("Difficulty mode", ["Balanced", "Easy only", "Medium only", "Hard only"])

if st.button("Generate Quiz"):
    st.info("Quiz backend is not connected yet. This page is currently a UI skeleton.")

    st.write(
        {
            "topic": topic,
            "num_questions": num_questions,
            "question_type": question_type,
            "difficulty_mode": difficulty_mode,
        }
    )