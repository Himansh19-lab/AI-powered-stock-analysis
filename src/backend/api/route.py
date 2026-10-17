

from google.api.http_pb2 import Http
from langchain_core.messages import HumanMessage, AIMessage
from fastapi import status
import os
from  fastapi import APIRouter, HTTPException, FastAPI
from fastapi.responses import StreamingResponse
from pathlib import Path
import shutil


from backend.pipeline.rag_pipeline import FinancialRAGPipeline
from backend.utils.logger import Logger
from backend.api.schema import (
    ChatRequest,
    ChatResponse,
    ReportRequest, 
    ReportResponse,
    UploadResponse,
    CompanyListResponse
)


logger = Logger(name="APIRoute", log_file="api_route.log", level="DEBUG")

DATA_DIR = Path(__file__).resolve().parents[3] / 'data'
CHROMA_DB = Path(__file__).resolve().parents[3] / 'storage'/ 'chroma'
pipeline = FinancialRAGPipeline()

app = FastAPI(title="AI-powered Stock Analysis", version="1.0.0")

router = APIRouter(prefix='/api/v1', tags=['Financial RAG'])


@router.get('/health', status_code=status.HTTP_200_OK, tags=['Health'])
async def health_check():
    return {"status": "ok"}


@router.post('/report', response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    try:
        logger.info(f"Generating financial report for {request.company_name}")
        report = pipeline.build_financial_report_chain(request.company_name, request.source_pdf)
        return ReportResponse(company_name=request.company_name, report=report)
    except Exception as e:
        logger.error(f"Error generating financial report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate financial report")


@router.post('/chat', response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    logger.info(f"Generating chat response for {request.company_name} for the query {request.query}")

    try:
        history = []
        if request.chat_history:
            for msg in request.chat_history:
                if msg.role == "user":
                    history.append(HumanMessage(content=msg.content))
                else:
                    history.append(AIMessage(content=msg.content))
        if request.stream:
            stream_gen = pipeline.build_conversational_rag_chain(
                    query=request.query,
                    company_name=request.company_name,
                    source_pdf_file=request.source_pdf,
                    chat_history=history,
                    stream=True
                )
            return StreamingResponse(stream_gen, media_type='text/event-stream')
        else:
            ai_message = pipeline.build_conversational_rag_chain(
                query=request.query,
                company_name=request.company_name,
                source_pdf_file=request.source_pdf,
                chat_history=history,
                stream=False
            )
            if ai_message is None:
                raise HTTPException(status_code=500,detail="Failed to generate chat response")

            logger.info(f"Generated chat response for {request.company_name}")
            return ChatResponse(
                query=request.query,
                answer=ai_message,
                source=request.source_pdf
            )
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error generating chat response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate chat response")

# Attach router to FastAPI AFTER defining all routes
app.include_router(router)