from pprint import pprint

from src.agents.crew import qa_crew


# input_data = {
#     "user_query": "Explain about adaptive radiation",
#     "chat_history": "{}"
# }

input_data = {
    "user_query": "Explain briefly about parallel architecture in microprocessors",
    "chat_history": {}
}

result = qa_crew.kickoff(input_data)

result_dict = result.to_dict()

pprint(result_dict)