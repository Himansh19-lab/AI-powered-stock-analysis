from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_companies_endpoint(client: TestClient):
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert isinstance(data["files"], list)


def test_upload_non_pdf_rejected(client: TestClient):
    files = {"file": ("test.txt", b"some text content", "text/plain")}
    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 400
    assert "Only PDF files are currently supported" in response.json()["detail"]


@patch("backend.api.route.pipeline.build_financial_report_chain")
def test_report_endpoint_success(mock_report_chain, client: TestClient):
    mock_report_chain.return_value = "### Financial Report for Apple\nNet sales: $391B"

    payload = {
        "company_name": "Apple",
        "source_pdf": "NASDAQ_AAPL_2025.pdf"
    }
    response = client.post("/api/v1/report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Apple"
    assert "Financial Report for Apple" in data["report"]


@patch("backend.api.route.pipeline.build_conversational_rag_chain")
def test_chat_endpoint_non_streaming(mock_chat_chain, client: TestClient):
    mock_chat_chain.return_value = "Apple's net sales in 2025 were $391.0 billion."

    payload = {
        "query": "What were the net sales?",
        "company_name": "Apple",
        "source_pdf": "NASDAQ_AAPL_2025.pdf",
        "chat_history": [],
        "stream": False
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "What were the net sales?"
    assert "391.0 billion" in data["answer"]
    assert data["source"] == "NASDAQ_AAPL_2025.pdf"


@patch("backend.api.route.pipeline.build_conversational_rag_chain")
def test_chat_endpoint_streaming(mock_chat_chain, client: TestClient):
    def fake_stream():
        yield "Apple "
        yield "revenue "
        yield "grew."

    mock_chat_chain.return_value = fake_stream()

    payload = {
        "query": "How did revenue trend?",
        "company_name": "Apple",
        "source_pdf": "NASDAQ_AAPL_2025.pdf",
        "chat_history": [],
        "stream": True
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "Apple revenue grew." in response.text
