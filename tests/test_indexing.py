from pathlib import Path
import pytest
from langchain_core.documents import Document

from backend.indexing.document_loader import DocumentLoader, SupportedFormat
from backend.indexing.document_split import ChunkDocument
from backend.indexing.vector_store import VectorStore


def test_supported_formats():
    extensions = [ext.value[0] for ext in SupportedFormat]
    assert ".pdf" in extensions
    assert ".txt" in extensions


def test_document_loader_missing_file():
    loader = DocumentLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_from_file(Path("non_existent_file.pdf"))


def test_chunk_document_splitting():
    chunker = ChunkDocument(chunk_size=100, chunk_overlap=20)
    sample_text = "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories, and sells a variety of related services. " * 5
    docs = [Document(page_content=sample_text, metadata={"source": "test.pdf", "page": 1})]

    chunks = chunker.invoke(docs)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.metadata["source"] == "test.pdf"
        assert chunk.metadata["page"] == 1


def test_vector_store_deterministic_id_generation():
    doc1 = Document(page_content="Consolidated net sales were $100M", metadata={"source": "AAPL.pdf", "page": 10})
    doc2 = Document(page_content="Consolidated net sales were $100M", metadata={"source": "AAPL.pdf", "page": 10})
    doc3 = Document(page_content="Consolidated net sales were $200M", metadata={"source": "AAPL.pdf", "page": 10})

    id1 = VectorStore._get_ids(doc1)
    id2 = VectorStore._get_ids(doc2)
    id3 = VectorStore._get_ids(doc3)

    # Identical content + metadata produces identical hash
    assert id1 == id2
    # Different content produces distinct hash
    assert id1 != id3
