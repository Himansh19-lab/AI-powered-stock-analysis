
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from enum import Enum
from pathlib import Path
from typing import List
from backend.utils.CommonInterface import ComponentInterface
from backend.utils.logger import Logger

class SupportedFormat(Enum):
    PDF =  ".pdf", PyPDFLoader
    TXT = ".txt", TextLoader

class DocumentLoader(ComponentInterface):
    
    logger = Logger(name="Document Loader", log_file="document_loader.log", level="INFO")


    def invoke(self, path: Path) -> List[Document]:  
        """
        This method will check and the given document and load it based on the format
        If document is not found it will raise a FileNotFoundError
        If document format is not supported it will raise a ValueError
        Returns:
            list of documents

        """

        if not path.exists():
            self.logger.error(f"File not found : {path}")
            raise FileNotFoundError(f"File not found: {path}")

        ext = path.suffix.split(".")[-1].upper()
             
        try:
            loader_cls = SupportedFormat[ext].value[1]
            loader = loader_cls(path)
            self.logger.info(f"Loading document with format {loader_cls}")
            documents = loader.load()
            self.logger.info(f"Documents loaded successfully: {len(documents)}")
            return documents
        except KeyError as e:
            self.logger.error(f"Unsupported document format: {ext}")
            self.logger.error(e)
            raise ValueError("Unsupported document format")



if __name__ == "__main__":

    loader = DocumentLoader()
    documents = loader.invoke(Path("/Users/himanshu/Documents/IIIT_Bangalore/Git-repo/AI-powered-stock-analysis/data/NASDAQ_AAPL_2025.pdf"))
    
