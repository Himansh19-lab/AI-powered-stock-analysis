
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

class DocumentLoader:
    
    logger = Logger(name="Document Loader", log_file="document_loader.log", level="INFO")

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
            self.logger.info(f"Loading document with format {loader_cls}")
            documents = loader.load()
            for document in documents:
                document.metadata["source"] = file_path.name
            self.logger.info(f"Length of Documents loaded successfully: {len(documents)} from {file_path}" )
            return documents

        except KeyError as e:
            self.logger.error(f"Unsupported document format: {extension}")
            self.logger.error(e)
            raise ValueError(f"Unsupported document format: {extension}")


    def load_from_directory(self, dir_path: Path) -> List[List[Document]]:
        if not dir_path.exists():
            self.logger.error(f"Directory not found : {dir_path}")
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {dir_path}")

        all_documents: List[Document] = []

        for extension in SupportedFormat:
            pattern = f"*{extension.value[0]}"

            for file_path in sorted(dir_path.rglob(pattern)):
                try:
                    documents = self.load_from_file(file_path)
                    all_documents.extend(documents)
                except Exception:
                    self.logger.error(f"Failed to load {file_path}")
                    raise

        self.logger.info(
            f"Loaded {len(all_documents)} document(s) "
            f"from directory: {dir_path}"
        )

        return all_documents


if __name__ == "__main__":
    loader = DocumentLoader()
    documents = loader.load_from_directory(Path("/Users/himanshu/Documents/IIIT_Bangalore/Git-repo/AI-powered-stock-analysis/data/"))
    print(len(documents))
