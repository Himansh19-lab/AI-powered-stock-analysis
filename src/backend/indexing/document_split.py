from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.utils.logger import Logger
from backend.utils.CommonInterface import ComponentInterface
from langchain_core.documents import Document

from backend.indexing.document_loader import DocumentLoader

from typing import List


class ChunkDocument(ComponentInterface):
    logger = Logger(name="ChunkDocument", log_file="document_split.log", level="INFO")

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


    def invoke(self, documents: List[Document]) -> List[Document]:
        """
        This method will chunk the documents
        Returns:
            list of documents

        """
        self.logger.info(f"Chunking document with size {self.chunk_size} and overlap {self.chunk_overlap}")
        chunks = self.splitter.split_documents(documents)
        self.logger.info(f"Chunking completed. Total chunks: {len(chunks)}")
        return chunks


if __name__ == "__main__":
    loader = DocumentLoader()
    documents = loader.invoke(Path("/Users/himanshu/Documents/IIIT_Bangalore/Git-repo/AI-powered-stock-analysis/data"))
    chunker = ChunkDocument()
    chunks = chunker.invoke(documents)

