import logging
from pathlib import Path

import chromadb
from markitdown import MarkItDown
from llama_index.core import Document, VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.readers.file import PDFReader

# Load our configuration class.
from src.rag_doc_ingestion.config.doc_ingestion_settings import DocIngestionSettings


SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md"}

# Load the settings from the environment variables.
settings = DocIngestionSettings()

# Set up logging configuration.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load the embeddings model.
logger.info("Loading HuggingFace embedding model...")
embed_model = HuggingFaceEmbedding()


def get_supported_document_paths(docs_dir_path: str) -> list[Path]:
    """
    Returns all supported document files from a directory.

    Parameters:
        docs_dir_path (str): Directory containing uploaded documents.

    Returns:
        list[Path]: Supported document paths.
    """
    docs_dir = Path(docs_dir_path)

    if not docs_dir.exists():
        logger.warning(f"Document directory does not exist: {docs_dir_path}")
        return []

    return [
        file
        for file in docs_dir.iterdir()
        if file.is_file() and file.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS
    ]


def convert_document_to_markdown(file_path: Path) -> Document | None:
    """
    Converts one document to Markdown/Text using MarkItDown.

    Parameters:
        file_path (Path): Path to the uploaded source document.

    Returns:
        Document | None: LlamaIndex document containing converted text and metadata.
    """
    try:
        markitdown = MarkItDown()
        result = markitdown.convert(str(file_path))

        text_content = result.text_content if result else ""

        if not text_content or not text_content.strip():
            logger.warning(f"No text extracted from document: {file_path.name}")
            return None

        return Document(
            text=text_content,
            metadata={
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": file_path.suffix.lower(),
            },
        )

    except Exception as e:
        logger.error(f"MarkItDown conversion failed for {file_path.name}: {e}")
        return None


def load_uploaded_documents_with_markitdown(docs_dir_path: str) -> list[Document]:
    """
    Loads and converts all supported uploaded documents using MarkItDown.

    Parameters:
        docs_dir_path (str): Directory containing uploaded documents.

    Returns:
        list[Document]: Converted LlamaIndex documents.
    """
    documents = []

    supported_files = get_supported_document_paths(docs_dir_path)

    for file_path in supported_files:
        logger.info(f"Converting uploaded document with MarkItDown: {file_path.name}")

        converted_document = convert_document_to_markdown(file_path)

        if converted_document:
            documents.append(converted_document)

    return documents


def build_vector_store_from_documents():
    """
    Builds the original vector store from configured documents directory.

    This function is kept for backward compatibility with the original ingestion CLI.
    """
    logger.info("Starting vector store ingestion process.")

    try:
        docs_dir_path = settings.DOCUMENTS_DIR
        vector_store_path = settings.VECTOR_STORE_DIR
        collection_name = settings.COLLECTION_NAME

        print(f"[INGESTION] DOCUMENTS_DIR = {settings.DOCUMENTS_DIR}")
        print(f"[INGESTION] VECTOR_STORE_DIR = {settings.VECTOR_STORE_DIR}")
        print(f"[INGESTION] COLLECTION_NAME = {settings.COLLECTION_NAME}")

        logger.info(f"Loading documents from directory {docs_dir_path}")

        loader = SimpleDirectoryReader(
            input_dir=docs_dir_path,
            file_extractor={
                ".pdf": PDFReader()
            }
        )

        documents = loader.load_data()

        parser = SimpleNodeParser.from_defaults(
            chunk_size=1024,
            chunk_overlap=100,
        )

        nodes = parser.get_nodes_from_documents(documents)

        logger.info(f"Parsed {len(nodes)} nodes")
        logger.info(f"Initializing ChromaDB persistent client at: {vector_store_path}")

        db = chromadb.PersistentClient(path=vector_store_path)

        chroma_collection = db.get_or_create_collection(name=collection_name)

        logger.info("Creating Chroma vector store")

        vector_store = ChromaVectorStore(
            chroma_collection=chroma_collection
        )

        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )

        logger.info("Building vector store index")

        VectorStoreIndex(
            nodes,
            storage_context=storage_context,
            vector_store=vector_store,
            embed_model=embed_model,
        )

        logger.info("Vector store built successfully")
        return 0

    except Exception as e:
        logger.error(f"Error during vector store build: {e}")
        return 1


def build_vector_store_from_uploaded_documents(
    docs_dir_path: str,
    vector_store_path: str,
    collection_name: str = "document_collection",
):
    """
    Builds a user-specific ChromaDB vector store from uploaded documents.

    Supports:
    - PDF
    - DOCX
    - PPTX
    - TXT
    - MD

    Parameters:
        docs_dir_path (str): User upload directory.
        vector_store_path (str): User-specific ChromaDB directory.
        collection_name (str): ChromaDB collection name.

    Returns:
        int: 0 if ingestion succeeds, 1 if ingestion fails.
    """
    logger.info("Starting uploaded document ingestion process.")

    try:
        print(f"[UPLOAD INGESTION] DOCUMENTS_DIR = {docs_dir_path}")
        print(f"[UPLOAD INGESTION] VECTOR_STORE_DIR = {vector_store_path}")
        print(f"[UPLOAD INGESTION] COLLECTION_NAME = {collection_name}")

        documents = load_uploaded_documents_with_markitdown(docs_dir_path)

        if not documents:
            logger.warning("No uploaded documents found for ingestion.")
            return 1

        parser = SimpleNodeParser.from_defaults(
            chunk_size=1024,
            chunk_overlap=100,
        )

        nodes = parser.get_nodes_from_documents(documents)

        if not nodes:
            logger.warning("No nodes created from uploaded documents.")
            return 1

        logger.info(f"Parsed {len(nodes)} nodes from uploaded documents")

        logger.info(
            f"Initializing uploaded ChromaDB persistent client at: {vector_store_path}"
        )

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
            embed_model=embed_model,
        )

        logger.info(
            f"Uploaded Chroma collection count after ingestion: {chroma_collection.count()}"
        )
        logger.info("Uploaded document vector store built successfully")

        return 0

    except Exception as e:
        logger.error(f"Error during uploaded document vector store build: {e}")
        return 1


if __name__ == "__main__":
    build_vector_store_from_documents()