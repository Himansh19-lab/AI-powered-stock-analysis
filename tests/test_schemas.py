import pytest
from pydantic import ValidationError
from backend.api.schema import (
    ChatMessageSchema,
    ChatRequest,
    ChatResponse,
    ReportRequest,
    ReportResponse,
    UploadResponse,
    CompanyListResponse,
)


def test_chat_message_schema():
    msg = ChatMessageSchema(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"

    with pytest.raises(ValidationError):
        ChatMessageSchema(role="invalid_role", content="Hello")


def test_chat_request_defaults():
    req = ChatRequest(query="What was net sales?", company_name="Apple")
    assert req.query == "What was net sales?"
    assert req.company_name == "Apple"
    assert req.source_pdf is None
    assert req.chat_history == []
    assert req.stream is False


def test_chat_request_with_history():
    req = ChatRequest(
        query="Follow-up question",
        company_name="Apple",
        source_pdf="NASDAQ_AAPL_2025.pdf",
        chat_history=[
            ChatMessageSchema(role="user", content="Hi"),
            ChatMessageSchema(role="assistant", content="Hello! How can I help?"),
        ],
        stream=True,
    )
    assert len(req.chat_history) == 2
    assert req.stream is True
    assert req.source_pdf == "NASDAQ_AAPL_2025.pdf"


def test_report_request_validation():
    req = ReportRequest(company_name="Tesla", source_pdf="NASDAQ_TSLA_2022.pdf")
    assert req.company_name == "Tesla"
    assert req.source_pdf == "NASDAQ_TSLA_2022.pdf"

    # Missing required company_name
    with pytest.raises(ValidationError):
        ReportRequest()


def test_upload_response_model():
    res = UploadResponse(
        filename="NASDAQ_AAPL_2025.pdf",
        message="Indexed successfully",
        chunks_indexed=42,
    )
    assert res.filename == "NASDAQ_AAPL_2025.pdf"
    assert res.chunks_indexed == 42


def test_company_list_response_model():
    res = CompanyListResponse(files=["AAPL.pdf", "NVDA.pdf"])
    assert len(res.files) == 2
