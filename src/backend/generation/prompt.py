
from xml.dom.minidom import DocumentFragment
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document

# ==============================================================================
# MODE 1: STRUCTURED FINANCIAL ANALYSIS REPORT
# ==============================================================================
FINANCIAL_REPORT_SYSTEM_PROMPT = """You are a Principal Financial Analyst and CFA charterholder.
Your task is to generate a comprehensive, executive-ready Fundamental Analysis Report for {company_name} based strictly on the provided annual report (Form 10-K).
Structure your report into the following clear markdown sections:
# 📊 Financial & Operational Analysis: {company_name}
### 1. 📈 Executive Summary & Revenue Performance
- Total Net Sales / Revenue for the current fiscal year vs previous fiscal year.
- Revenue growth rate (percentage change) and whether it met company expectations.
### 2. 💰 Profitability & Margins
- Gross Profit and Gross Margin (%).
- Operating Expenses breakdown (R&D, Selling & Administrative).
- Operating Income and Net Income (%).
### 3. 🧩 Key Segment Breakdown
- Performance across major product or geographic business segments.
- Which segments drove growth and which underperformed.
### 4. ⚠️ Key Risks & Future Outlook
- Top 2-3 material risks or headwinds highlighted in the filing.
- Management's commentary or strategic focus for the upcoming year.
---
### RULES:
- Use exact figures and state units clearly (e.g., "$416,161 million" or "$416.16 billion").
- Every key metric must cite the source page: `[Page X]`.
- If a section cannot be fully populated from the context, explicitly state: "Data not available in provided document excerpts."
### CONTEXT:
{context}
"""
financial_report_prompt = ChatPromptTemplate.from_messages([
    ("system", FINANCIAL_REPORT_SYSTEM_PROMPT),
    ("human", "Generate the comprehensive financial analysis report for {company_name}."),
])


# ==============================================================================
# MODE 2: INTERACTIVE LIVE CONVERSATIONAL CHATBOT
# ==============================================================================
CONTEXTUALIZE_Q_SYSTEM_PROMPT = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""
contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])


CHATBOT_SYSTEM_PROMPT  = """You are an interactive AI Financial Research Assistant for {company_name}.
You help users explore and understand the company's financial results and annual reports.
### INSTRUCTIONS:
1. Answer the user's question accurately using the provided document context and conversation history.
2. In corporate filings (10-K), terms like "Net Sales", "Total Revenue", and "Top-line Sales" are synonymous. Treat them as interchangeable.
3. If the user asks a follow-up question, use the conversation history to understand context.
4. Keep answers concise, factual, and backed by figures.
5. Always include page citations where possible: `[Source: {company_name}, Page X]`.
6. If neither the context nor the history contains enough data to answer, politely say:
   "I could not find that information in the provided reports for {company_name}."
---
### CONTEXT:
{context}
"""


# Uses MessagesPlaceholder to support dynamic conversation history (chat_history)
conversational_rag_prompt = ChatPromptTemplate.from_messages([
    ("system", CHATBOT_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])

def _format_documents_source(docs: Document) -> str:
    """Format the documents for the prompt comes from retriever """
    formated_chunk = []
    for doc in docs:
        source = doc.metadata.get('source', "Document")
        chunk = doc.page_content
        page = doc.metadata.get('page','NA')
        chunk_header = f" -- File: {source} | Page: {page}\n"
        formated_chunk.append(chunk_header+chunk)
    return '\n\n'.join(formated_chunk)




if __name__ == "__main__":
    # Quick sanity check
    print("Prompts defined successfully:")
    print("1. Financial Report Prompt Input Variables:", financial_report_prompt.input_variables)
    print("2. Conversational RAG Prompt Input Variables:", conversational_rag_prompt.input_variables)