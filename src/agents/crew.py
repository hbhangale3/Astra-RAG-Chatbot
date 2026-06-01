from crewai import Crew

from src.agents.agent.question_answer_agent import qa_agent
from src.agents.tasks.question_answer_task import qa_task


qa_crew = Crew(
    agents=[qa_agent],
    tasks=[qa_task],
    verbose=True,
)