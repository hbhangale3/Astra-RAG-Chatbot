import logging

import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

#load our configuration class
from src.rag_doc_ingestion.config.doc_ingestion_settings import DocIngestionSettings

#load the settinsgs from the environment variables
settings = DocIngestionSettings()

#set up logging configuration
logging.basicConfig(
    level = logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

#load the embeddings model
logger.info("Loading HuggingFace embedding model...")
embed_model = HuggingFaceEmbedding()


#define the function for vector store

def build_vector_store_from_documents():
    logger.info("Starting vector store ingestion process.")
    try:

        #get the variables from the settings
        docs_dir_path = settings.DOCUMENTS_DIR
        vector_store_path = settings.VECTOR_STORE_DIR
        collection_name = settings.COLLECTION_NAME

        logger.info(f"Loading documents from directory {docs_dir_path}")
        loader = SimpleDirectoryReader(input_dir=docs_dir_path)
        documents=loader.load_data()
        #now we need to create chunks of the loaded documents
        parser = SimpleNodeParser.from_defaults(chunk_size=1024,chunk_overlap=100)
        nodes = parser.get_nodes_from_documents(documents)
        logger.info(f"Parsed {len(nodes)} nodes")
        logger.info(f"initializing ChromaDB persistent client at: {vector_store_path}")
        db=chromadb.PersistentClient(path=vector_store_path)
        #create or retrieve the vector collection
        chorma_collection = db.get_or_create_collection(name=collection_name)
        logger.info(f"Creating Chroma vector store")

        vector_store = ChromaVectorStore(chroma_collection=chorma_collection)

        #create storage context
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        logger.info("Building vector store index")
        index = VectorStoreIndex(
            nodes,
            storage_context=storage_context,
            vector_store=vector_store,
            embed_model=embed_model
        )
        logger.info("vector store build successfully")
        return 0
    except Exception as e:
        logger.error(f"Error during vector store build: {e}")
        return 1


if __name__ == "__main__":
    build_vector_store_from_documents()