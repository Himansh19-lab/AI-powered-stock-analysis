
from typing_extensions import Union
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
    
    logger = Logger(name="DocumentLoader", log_file="document_loader.log", level="INFO")

    document_supported = [ "*"+ext.value[0] for ext in SupportedFormat]
    
    def load_from_file(self, file_path: Path) -> List[Document]:
        """
        This method will load the document from the given file path
        If document is not found it will raise a FileNotFoundError
        If document format is not supported it will raise a ValueError
        Returns:
            list of documents

        """

        if not file_path.exists():
            self.logger.error(f"File not found : {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            self.logger.error(f"Provide path is not a file: {file_path}")
            raise ValueError(f"Provide path is not a file: {file_path}")

        extension = file_path.suffix.split(".")[-1].upper()
             
        try:
            loader_cls = SupportedFormat[extension].value[1]
            loader = loader_cls(str(file_path))
            self.logger.info(f"Loading file: {file_path}")
            self.logger.info(f"File name: {file_path.name}")
            documents = loader.load()
            for document in documents:
                document.metadata["source"] = file_path.name
            self.logger.info(f"Length of Documents: {len(documents)}" )
            return documents

        except KeyError as e:
            self.logger.error(f"Unsupported document format: {extension}")
            self.logger.error(e)
            raise ValueError(f"Unsupported document format: {extension}")


    def load_from_directory(self, dir_path: Path) -> List[Document]:
        if not dir_path.exists():
            self.logger.error(f"Directory not found : {dir_path}")
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {dir_path}")

        all_documents: List[Document] = []
        for file in sorted(dir_path.glob("*")):
            if file.is_file() and file.suffix.lstrip(".").upper() in SupportedFormat.__members__:
                try:
                    documents = self.load_from_file(file)
                    all_documents.extend(documents)
                except Exception:
                    self.logger.error(f"Failed to load {file}")
                    raise
            else:
                self.logger.error(f"File not supported: {file}")
        self.logger.info(f"All documents loaded from directory. Total: {len(all_documents)}")
        return all_documents


    def invoke(self, input_path: str | Path ) -> List[Document]:
        """
        Unified entry point routes to file or directory loader automatically.
        Returns a list of documents, sorted by filename
        """

        input_path = Path(input_path)
        if input_path.is_file():
            return self.load_from_file(input_path)
        elif input_path.is_dir():
            return self.load_from_directory(input_path)
        else:
            self.logger.error(f"Unsupported input path: {input_path}")
            raise ValueError(f"Unsupported input path: {input_path}")

if __name__ == "__main__":
    loader = DocumentLoader()
    documents = loader.invoke(Path("/Users/himanshu/Documents/IIIT_Bangalore/Git-repo/AI-powered-stock-analysis/data"))

