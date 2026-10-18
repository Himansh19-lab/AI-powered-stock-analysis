
from typing import List, Tuple, Optional
import os
import hashlib
from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain.embeddings import init_embeddings
from  dotenv import load_dotenv
from backend.utils.CommonInterface import ComponentInterface
from backend.indexing.document_loader import DocumentLoader
from backend.indexing.document_split import ChunkDocument
from backend.utils.logger import Logger


from backend.utils.config import config

class VectorStore(ComponentInterface):
    logger = Logger(name="VectorStore", log_file="vector_store.log", level="INFO")

    def __init__(self, vector_store_path: Path = None, embeddings=None, collection_name: Optional[str] = None) -> None:
        

        self.vector_store_path = vector_store_path or config.paths.chroma_db
        self.vector_store_path.mkdir(parents=True, exist_ok=True)

        embedding_model = config.embeddings.model_name
        embed_kwargs = {}
        if embedding_model.startswith("bedrock:"):
            embed_kwargs["region_name"] = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        self.embeddings = embeddings or init_embeddings(model=embedding_model, **embed_kwargs)

        self.collection_name = collection_name or config.storage.collection_name
        self._vector_store = Chroma(
            persist_directory=self.vector_store_path, 
            embedding_function=self.embeddings, 
            collection_name=self.collection_name)
    
    @property
    def store(self) -> Chroma:
        """
        Getter for underlying Chroma database instance.
        """
        return self._vector_store
  
    def _deduplicate_documents(self, docs: list[Document]) -> Tuple[List[str], List[Document]]:
        """
        This method is for de duplicating the documents before inserting into the vector store.
        It will check for the duplicate documents based on the metadata and page content

        Args:
            docs (list[Document]): List of documents to be de duplicated

        Returns:
            Tuple[List[str], List[Document]]: Tuple of unique ids and unique documents

        """
        seen_ids = set()
        unique_ids = []
        unique_docs = []
        for chunk in docs:
            chunk_id = self._get_ids(chunk)
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_ids.append(chunk_id)
                unique_docs.append(chunk)
        
        self.logger.info(f"Filtered {len(docs) - len(unique_docs)} duplicate chunks.")
        self.logger.info(f"Adding {len(unique_docs)} unique documents to collection '{self.collection_name}'")
        return (unique_ids, unique_docs)

    def add_documents_to_vector_store(self, docs: list[Document], batch_size: int = 500) -> Chroma:
        if not docs:
            self.logger.warning("No documents provided to add to vector store.") 
            return self._vector_store

        unique_ids, unique_docs = self._deduplicate_documents(docs)
        total_docs = len(unique_docs)
        total_batches = (total_docs + batch_size - 1) // batch_size

        for idx, i in enumerate(range(0, total_docs, batch_size), start=1):
            batch_docs = unique_docs[i:i + batch_size]
            batch_ids = unique_ids[i:i + batch_size]
            self.logger.info(f"Adding batch {idx}/{total_batches} ({len(batch_docs)} documents) to ChromaDB...")
            self._vector_store.add_documents(batch_docs, ids=batch_ids)

        self.logger.info("All documents added successfully")
        return self._vector_store
    
    @staticmethod
    def _get_ids(chunk: Document):
        source = chunk.metadata.get('source', 'unknown')
        page_number = chunk.metadata.get('page', 0)
        page_content = chunk.page_content
        unique_str = f"{source}-{page_number}-{page_content}"
        return hashlib.sha256(unique_str.encode("utf-8")).hexdigest()
    
    def invoke(self, documents):
        return self.add_documents_to_vector_store(documents)


if __name__ == "__main__":
    load_dotenv()
    loader = DocumentLoader()
    documents = loader.invoke()
    chunker = ChunkDocument()
    chunks = chunker.invoke(documents)
    vector_store = VectorStore()
    vector_store.invoke(chunks)