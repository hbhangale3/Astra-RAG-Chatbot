import logging
from urllib import response
from crewai.tools import tool
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.core import Settings
import chromadb

#import config
from src.agents.config.agent_settings import AgentSettings

#get a looger instance
logger = logging.getLogger(__name__)

#download & load embedding model
logger.info
("Loading HuggingFace embedding model...")
embed_model = HuggingFaceEmbedding()


#define the RAG QA tool
def rag_query_tool(query: str)-> dict:
    """
     Answers a query by retrieving relevant documents and generating a response.
    Returns both the generated answer and the source file names from which the information was retrieved.

    Args:
        query (str): The input query string to be processed.

    Returns:
        dict: A dictionary with the following keys:
            - 'answer': The generated answer string.
            - 'source_files': List of source file names used for retrieval.

    Notes:
        - Requires properly configured AgentSettings and access to the vector store.
        - The function loads the embedding model and LLM each time it is called.
       """
    
    settings = AgentSettings()
    vector_store_path = settings.VECTOR_STORE_DIR
    collection_name = settings.COLLECTION_NAME

    #configure LLm
    Settings.llm = Groq(
        model = settings.MODEL_NAME,
        temperature = settings.MODEL_TEMPERATURE,
        api_key = settings.GROQ_API_KEY
    ) 

#load Chroma collection
    db = chromadb.PersistentClient(path=vector_store_path)
    chroma_collection = db.get_or_create_collection(name=collection_name)

    #connect to the vector store
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    #Load index from vector store
    logger.info("Loading vector store index from ChromaDB")
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context = storage_context,
        embed_model = embed_model
    )

    #Create the query engine
    query_engine = index.as_query_engine(similarity_top_k=3)

    #pass the query to the query engine and get the response
    logger.info("Querying the index with the provided query")
    response = query_engine.query(query)
    # print("\n====================")
    # print("TYPE OF RESPONSE")
    # print(type(response))

    # print("\n====================") 
    # print("FULL RESPONSE OBJECT")
    # print(response)

    # print("\n====================")
    # print("REPR RESPONSE")
    # print(repr(response))

    # print("\n====================")
    # print("RESPONSE.RESPONSE")
    # print(response.response)

    # print("\n====================")
    # print("REPR RESPONSE.RESPONSE")
    # print(repr(response.response))
    source_file_names = {
    metadata.get("file_name")
    for metadata in getattr(response, "metadata", {}).values()
    if metadata.get("file_name")
}
    return {
    "answer": str(response.response).replace("\x08", "").strip(),
    "source_files": list(source_file_names)
}

output = rag_query_tool(query="Explain about evolution very briefly in max 2 lines.")
print(output)
print(output["answer"])
print(output["source_files"])