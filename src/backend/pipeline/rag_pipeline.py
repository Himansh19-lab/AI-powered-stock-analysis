
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from typing import Optional, List

from backend.retriever.retriever import RAGRetriever
from backend.generation.llm import LLMFactory
from backend.generation.prompt import financial_report_prompt, conversational_rag_prompt, _format_documents_source
from backend.utils.logger import Logger


class FinancialRAGPipeline:
    """
    End-to-end RAG Pipeline coordinating Retriever, Prompts, and LLM.
    Supports both:
    1. Comprehensive Financial Report Generation
    2. Interactive Conversational Chatbot
    """
    logger = Logger(name="FinancialRAGPipeline", log_file="FinancialRAGPipeline.log", level="DEBUG")
    
    def __init__(self,model_provider='openai',model_name='gpt-4o-mini',temperature=0.1):
        self.retriever = RAGRetriever()
        self.financial_report_prompt = financial_report_prompt
        self.conversational_rag_prompt = conversational_rag_prompt
        self.llm = LLMFactory.get_llm(model_name=model_name, model_provider=model_provider, temperature=temperature)
        self.parser = StrOutputParser()
        self.financial_report_chain = None
        self.conversational_rag_chain = None
        self.logger.info("Financial RAG Pipeline initiated")

    # =========================================================================
    # FEATURE 1: GENERATE STRUCTURED FINANCIAL ANALYSIS REPORT
    # =========================================================================
    #  Build the Financial Report Generation Chain

    def build_financial_report_chain(self, company_name: str, source_pdf_file: Optional[str]=None):
        """Builds the RAG chain for generating financial reports."""
        try:    
            self.logger.info("Building Financial Report Generation Chain")
            search_query = "Consolidated Statements of operations net sales revenue segment income risk factor"
            
            retrieved_docs = self.retriever.invoke(search_query, filter_by_source=source_pdf_file)
            
            formated_retrieved_docs = _format_documents_source(retrieved_docs)
            # Build a RunnablePassthrough that pulls context from the retriever
            self.financial_report_chain = (
                {   "context": RunnablePassthrough(),
                    "company_name": RunnablePassthrough()
                }
                | self.financial_report_prompt
                | self.llm
                | self.parser
            )

            self.logger.info("Financial Report Generation Chain built successfully")
            response = self.financial_report_chain.invoke({
                "context": formated_retrieved_docs,
                "company_name": company_name
            })
            
            return response
        except Exception as e:
            self.logger.error(f"Error building Financial Report Generation Chain: {e}")
            return None
 
    def build_conversational_rag_chain(self, query: str, company_name: str, 
                    source_pdf_file: Optional[str]=None,
                    chat_history: Optional[List] =None, stream: Optional[bool]=False):
        """Builds the RAG chain for interactive chatbot queries."""
        try:
            chat_history = chat_history or []
            self.logger.info("Building Conversational RAG Chain")
            
            retrieved_docs = self.retriever.invoke(query, filter_by_source=source_pdf_file)
            
            formated_retrieved_docs = _format_documents_source(retrieved_docs)
            # Build a RunnablePassthrough that pulls context from the retriever
            self.conversational_rag_chain = (
                self.conversational_rag_prompt
                | self.llm
                | self.parser
            )

            input_data = {
                "context": formated_retrieved_docs,
                "question": query,
                "company_name": company_name,
                "chat_history": chat_history
            }
            if stream:
                self.logger.info("Conversational RAG Chain built successfully (Stream)")
                return self.conversational_rag_chain.stream(input_data)

            self.logger.info("Conversational RAG Chain built successfully (Invoke)")
            return self.conversational_rag_chain.invoke(input_data)
            
            
        except Exception as e:
            self.logger.error(f"Error building Conversational RAG Chain: {e}")
            return None   

if __name__ == "__main__":
    pipeline = FinancialRAGPipeline()
    report = pipeline.build_financial_report_chain("Apple", "NASDAQ_AAPL_2025.pdf")
    print(report)   

    print("\n--- 2. Testing Chatbot ---")
    chat_answer = pipeline.build_conversational_rag_chain(
        query="What was the total net sales of Apple in fiscal year 2025?",
        company_name="Apple",
        source_pdf_file="NASDAQ_AAPL_2025.pdf"
    )
    print("Chat Answer:\n", chat_answer)