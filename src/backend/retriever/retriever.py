


from pathlib import Path
from langchain_core.documents import Document
from langchain.embeddings import init_embeddings
from langchain_chroma import Chroma
from typing import Optional, List
import os
from dotenv import load_dotenv

from backend.utils.CommonInterface import ComponentInterface
from backend.utils.logger import Logger

from backend.utils.config import config

class RAGRetriever(ComponentInterface):
    """ 
    A retriever class for RAG-based retrieval.
    """

    logger = Logger(name="RAGRetriever", log_file="retriever.log", level="INFO")

    def __init__(self, vector_store_path: Optional[Path] = None, 
                embeddings=None, collection_name: Optional[str] = None,
                top_k: Optional[int] = None, search_type: Optional[str] = None) -> None:
        
        self.vector_store_path = vector_store_path or Path(__file__).resolve().parents[3] / "storage/chroma"
        embedding_model = config.embeddings.model_name
        self.embeddings = embeddings or init_embeddings(model=embedding_model)
        self.top_k = top_k or config.retriever.top_k
        self.search_type = search_type or config.retriever.search_type
        self.collection_name = collection_name or config.storage.collection_name
        
        self.vector_store = Chroma(
            persist_directory=self.vector_store_path,
            embedding_function=self.embeddings,
            collection_name=self.collection_name
        )
        self.retriever = self.vector_store.as_retriever(search_type=self.search_type, search_kwargs={"k": self.top_k})
        self.logger.info("RAG Retreiver Initilaized ..")
    
    
    def invoke(self, query: str, filter_by_source: Optional[str]=None) -> List[Document]:
        """
        Retrieves relevant document chunks for a given query.
        Optionally filters by company PDF (e.g., 'NASDAQ_AAPL_2025.pdf').
        """
        self.logger.info(f"Retrieving top {self.top_k} chunks for query: '{query}'")
        if filter_by_source:
            self.logger.info(f"Filtering documents by source: {filter_by_source}")
            search_kwargs = {"k": self.top_k, "filter": {"source": filter_by_source}}
            filtered_retriever = self.vector_store.as_retriever(
                search_type=self.search_type,
                search_kwargs=search_kwargs
            )
            retrieved_documents = filtered_retriever.invoke(query)
        else:
            retrieved_documents = self.retriever.invoke(query)
        self.logger.info(f"Retreived {len(retrieved_documents)} documents")
        return retrieved_documents


if __name__ == "__main__":
    load_dotenv()
    
    rag_retriever = RAGRetriever()
    query = "What is the revenue of Apple?"
    company_name = "NASDAQ_AAPL_2025.pdf"
    documents = rag_retriever.invoke(query, filter_by_source=company_name)
    for doc in documents:
        print(doc.page_content)


        



        