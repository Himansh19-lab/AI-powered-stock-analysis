

from fastapi import UploadFile,File
from langchain_core.messages import HumanMessage, AIMessage
from fastapi import status
import os
from  fastapi import APIRouter, HTTPException, FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil



from backend.pipeline.rag_pipeline import FinancialRAGPipeline
from backend.indexing.document_loader import DocumentLoader
from backend.indexing.document_split import ChunkDocument
from backend.indexing.vector_store import VectorStore

from backend.utils.logger import Logger
from backend.api.schema import (
    ChatRequest,
    ChatResponse,
    ReportRequest, 
    ReportResponse,
    UploadResponse,
    CompanyListResponse
)


from backend.utils.config import config

logger = Logger(name="APIRoute", log_file="api_route.log", level="DEBUG")

DATA_DIR = config.paths.data_dir
CHROMA_DB = config.paths.chroma_db
pipeline = FinancialRAGPipeline()

app = FastAPI(title="AI-powered Stock Analysis", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix='/api/v1', tags=['Financial RAG'])


@router.get('/health', status_code=status.HTTP_200_OK, tags=['Health'])
async def health_check():
    return {"status": "ok"}


@router.post('/report', response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    try:
        logger.info(f"Generating financial report for {request.company_name}")
        report = pipeline.build_financial_report_chain(request.company_name, request.source_pdf)
        if report is None:
            raise HTTPException(status_code=500, detail="Failed to generate financial report")

        return ReportResponse(company_name=request.company_name, report=report)
    except HTTPException:   
        raise

    except Exception as e:
        logger.error(f"Error generating financial report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate financial report")


@router.post('/chat')
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


@router.post("/upload",response_model=UploadResponse)
def upload(file: UploadFile = File(...)):
    """
    Upload a company's annual report PDF and index it into ChromaDB.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are currently supported."
        )
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_path = DATA_DIR / file.filename
    
    if not file_path.exists():

        logger.info(f"Saving uploaded file to {file_path} ")
        try:
            with open(file_path, 'wb') as buffer:
                shutil.copyfileobj(file.file, buffer)

            # 1. Load Document
            loader = DocumentLoader()
            documents = loader.invoke(file_path)

            # 2. Chunk
            chunker = ChunkDocument()
            chunks = chunker.invoke(documents)

            # Vector store
            vectore_store = VectorStore(vector_store_path=CHROMA_DB, embeddings=pipeline.retriever.embeddings)
            vectore_store.invoke(chunks)    

            logger.info(f"Successfully indexed {file.filename} into vector store")
            return UploadResponse(
                filename=file.filename,
                message="File uploaded and indexed successfully.",
                chunks_indexed=len(chunks)
                )
        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file")
            
    else:
        logger.info(f"File {file.filename} already exists in vector store")
        return UploadResponse(
            filename=file.filename,
            message="File already exists in vector store.",
            chunks_indexed=0
        )

@router.get("/companies", response_model=CompanyListResponse)
async def list_companies():
    """
    List all uploaded company report PDFs available in the data directory.
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        pdf_files = [f.name for f in DATA_DIR.glob("*.pdf")]
        logger.info(f"Retrieved {len(pdf_files)} company PDF files")
        return CompanyListResponse(files=pdf_files)
    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve company files"
        )

# Attach router to FastAPI AFTER defining all routes
app.include_router(router)