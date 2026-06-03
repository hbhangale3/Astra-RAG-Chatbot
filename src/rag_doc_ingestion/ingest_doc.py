import logging

import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.readers.file import PDFReader
from numpy import rint

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

        #debug code to check the loaded settings
        print(f"[INGESTION] DOCUMENTS_DIR = {settings.DOCUMENTS_DIR}")
        print(f"[INGESTION] VECTOR_STORE_DIR = {settings.VECTOR_STORE_DIR}")
        print(f"[INGESTION] COLLECTION_NAME = {settings.COLLECTION_NAME}")
        
        logger.info(f"Loading documents from directory {docs_dir_path}")
        loader = SimpleDirectoryReader(
            input_dir=docs_dir_path,
            file_extractor={
                ".pdf":PDFReader()
            }
        )
        documents = loader.load_data()
        #debug code to check the loaded documents
        # print("=" * 100)
        # print(type(documents[0]))
        # print(documents[0].metadata)
        # print(documents[0].text[:3000])
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



#custom function to handle ingestion process for documents uploaded via the frontend.
def build_vector_store_from_uploaded_documents(
    docs_dir_path: str,
    vector_store_path: str,
    collection_name: str = "document_collection",
):
    logger.info("Starting uploaded document ingestion process.")

    try:
        print(f"[UPLOAD INGESTION] DOCUMENTS_DIR = {docs_dir_path}")
        print(f"[UPLOAD INGESTION] VECTOR_STORE_DIR = {vector_store_path}")
        print(f"[UPLOAD INGESTION] COLLECTION_NAME = {collection_name}")

        logger.info(f"Loading uploaded documents from directory {docs_dir_path}")

        loader = SimpleDirectoryReader(
            input_dir=docs_dir_path,
            file_extractor={
                ".pdf": PDFReader()
            }
        )

        documents = loader.load_data()

        if not documents:
            logger.warning("No uploaded documents found for ingestion.")
            return 1

        parser = SimpleNodeParser.from_defaults(
            chunk_size=1024,
            chunk_overlap=100
        )

        nodes = parser.get_nodes_from_documents(documents)

        if not nodes:
            logger.warning("No nodes created from uploaded documents.")
            return 1

        logger.info(f"Parsed {len(nodes)} nodes from uploaded documents")

        logger.info(f"Initializing uploaded ChromaDB persistent client at: {vector_store_path}")
        db = chromadb.PersistentClient(path=vector_store_path)

        try:
            db.delete_collection(name=collection_name)
            logger.info(f"Deleted existing uploaded document collection: {collection_name}")
        except Exception:
            logger.info(f"No existing uploaded document collection found: {collection_name}")

        chroma_collection = db.get_or_create_collection(name=collection_name)

        logger.info("Creating uploaded document Chroma vector store")

        vector_store = ChromaVectorStore(
            chroma_collection=chroma_collection
        )

        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )

        logger.info("Building uploaded document vector store index")

        VectorStoreIndex(
            nodes,
            storage_context=storage_context,
            vector_store=vector_store,
            embed_model=embed_model
        )
        logger.info(f"Uploaded Chroma collection count after ingestion: {chroma_collection.count()}")
        logger.info("Uploaded document vector store built successfully")
        return 0

    except Exception as e:
        logger.error(f"Error during uploaded document vector store build: {e}")
        return 1

if __name__ == "__main__":
    build_vector_store_from_documents()