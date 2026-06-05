import logging
from src.agents.crew import qa_crew


logger = logging.getLogger(__name__)

def get_answer(chat_history: list, user_id: str) -> dict:

   logger.info(f"Received chat history: {chat_history}")
   last_user_message = chat_history[-1]
   user_query = last_user_message["content"]
   logger.info(f"Extracted user query: {user_query}")
   logger.info(f"Using user_id for chat retrieval: {user_id}")

   #remove the last user message from the chat history to avoid duplication
   history_without_last_message = chat_history[:-1]
   input_data = {
         "user_query": user_query,
         "chat_history": history_without_last_message,
         "user_id": user_id
    }
   result = qa_crew.kickoff(input_data)
   result_dict = result.to_dict()
   return result_dict


# sample_chat_history = [
#     {"role": "user", "content": "What is Evolution?"},
#     {"role": "assistant", "content": "Evolution is the scientific theory describing how all life forms on Earth change over successive generations through alterations in their genetic material, leading to the diversity of life seen today. This process involves changes in an organism's genetic makeup (genome), which result from processes like mutation and are influenced by natural selection, where individuals with advantageous traits for their environment leave more offspring."},
#     {"role": "user", "content": "Explain in detail"}
# ]
# response = get_answer(sample_chat_history)
# print(response)