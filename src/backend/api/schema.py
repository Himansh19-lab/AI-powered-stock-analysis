from typing_extensions import List
from langchain_core import chat_history
from pydantic import BaseModel, Field
from typing import Optional, Annotated, Literal


class ChatMessageSchema(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):

    query: Annotated[str, Field(description="The user question")]
    company_name: Annotated[str, Field(description="The company name being queried")]
    source_pdf: Annotated[Optional[str], Field(default=None, description="The path to the source PDF")]
    chat_history: List[ChatMessageSchema] = Field(default_factory=list, description="The chat history")
    stream: bool = Field(default=False, description="Enable streaming for real-time response")

class ChatResponse(BaseModel):

    query : Annotated[str,Field(description="The user question")]
    answer : Annotated[str,Field(description="The answer to the query")]
    source : Annotated[Optional[str],Field(default=None,description="The source of the answer")]

class ReportRequest(BaseModel):
    company_name: str = Field(..., description="Company name (e.g. Apple)")
    source_pdf: Optional[str] = Field(default=None, description="Filename filter (e.g. NASDAQ_AAPL_2025.pdf)")

class ReportResponse(BaseModel):
    company_name: str
    report: str


class UploadResponse(BaseModel):
    filename: str
    message: str
    chunks_indexed: int

class CompanyListResponse(BaseModel):
    files: List[str]