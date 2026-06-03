from crewai import LLM
import os
from dotenv import load_dotenv
load_dotenv()
from src.agents.llm.llm_configuration import LLM_CONFIG


def get_llm_for_agent(agent_name):
    # model = LLM_CONFIG.get(agent_name, {}).get("model", "groq/llama-3.3-70b-versatile")
    # temperature = LLM_CONFIG.get(agent_name, {}).get("temperature", 0.2)
    return LLM(
        model="openai/gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.2
    )