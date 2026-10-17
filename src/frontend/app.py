import streamlit as st
import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"

# Page Configuration
st.set_page_config(
    page_title="AI-Powered Stock Analysis",
    page_icon="📈",
    layout="wide",          
    initial_sidebar_state="expanded"
)

# Custom CSS for polished styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        color: #1E3A8A;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .status-badge-ok {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-badge-err {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# Helper functions to talk to FastAPI
def check_backend_health():
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def get_available_companies():
    try:
        r = requests.get(f"{API_BASE_URL}/companies", timeout=5)
        if r.status_code == 200:
            return r.json().get("files", [])
    except Exception as e:
        st.sidebar.error(f"Failed to fetch files: {e}")
    return []


def upload_pdf(file_obj):
    try:
        files = {"file": (file_obj.name, file_obj.getvalue(), "application/pdf")}
        r = requests.post(f"{API_BASE_URL}/upload", files=files, timeout=120)
        return r.status_code, r.json()
    except Exception as e:
        return 500, {"detail": str(e)}


def generate_report(company_name, source_pdf):
    payload = {
        "company_name": company_name,
        "source_pdf": source_pdf if source_pdf else None
    }
    r = requests.post(f"{API_BASE_URL}/report", json=payload, timeout=180)
    if r.status_code == 200:
        return r.json().get("report", "")
    else:
        err = r.json().get("detail", "Error generating report")
        raise RuntimeError(err)


def stream_chat_response(query, company_name, source_pdf, chat_history):
    payload = {
        "query": query,
        "company_name": company_name,
        "source_pdf": source_pdf if source_pdf else None,
        "chat_history": chat_history,
        "stream": True
    }
    with requests.post(f"{API_BASE_URL}/chat", json=payload, stream=True, timeout=120) as r:
        if r.status_code != 200:
            yield f"⚠️ Error: {r.text}"
            return
        for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                yield chunk


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("⚙️ Control Panel")
    
    # Backend Status Indicator
    is_healthy = check_backend_health()
    if is_healthy:
        st.markdown('<span class="status-badge-ok">● Backend Online</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-err">● Backend Offline</span>', unsafe_allow_html=True)
        st.caption("Ensure `uvicorn` is running on port 8000.")

    st.divider()

    # Upload Section
    st.subheader("📄 Upload Annual Report")
    uploaded_file = st.file_uploader(
        "Upload Company PDF (10-K / Annual Report)",
        type=["pdf"],
        help="Upload PDF reports into ChromaDB vector storage."
    )

    if uploaded_file is not None:
        if st.button("🚀 Upload & Index Document", use_container_width=True):
            with st.spinner("Uploading and indexing chunks..."):
                status_code, res = upload_pdf(uploaded_file)
                if status_code == 200:
                    st.success(f"Indexed {res.get('chunks_indexed', 0)} chunks!")
                    st.rerun()
                else:
                    st.error(f"Upload failed: {res.get('detail', 'Unknown error')}")

    st.divider()

    # Document Selection
    st.subheader("🎯 Active Context")
    available_files = get_available_companies()
    
    selected_pdf = st.selectbox(
        "Select PDF Report",
        options=["None (Search All)"] + available_files,
        index=1 if available_files else 0,
        help="Select a specific PDF to ground the analysis and chat."
    )
    if selected_pdf == "None (Search All)":
        selected_pdf = None

    default_company = ""
    if selected_pdf:
        # Infer company name from filename e.g. "NASDAQ_AAPL_2025.pdf" -> "AAPL"
        parts = selected_pdf.replace(".pdf", "").split("_")
        default_company = parts[1] if len(parts) > 1 else parts[0]

    company_name = st.text_input(
        "Company Name",
        value=default_company or "Apple",
        help="Specify the target company name."
    )


# ---------------- MAIN CONTENT ----------------
st.markdown('<div class="main-header">📈 AI-Powered Financial Stock Analysis</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Deep RAG-powered financial intelligence from company annual reports (10-K/10-Q)</div>',
    unsafe_allow_html=True
)

tab_report, tab_chat = st.tabs(["📊 Financial Report Generator", "💬 Conversational Chatbot"])

# ---------------- TAB 1: FINANCIAL REPORT ----------------
with tab_report:
    st.subheader("Comprehensive Financial Analysis Report")
    st.write(
        f"Generate a deep financial report for **{company_name}**"
        + (f" filtered by `{selected_pdf}`." if selected_pdf else ".")
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        generate_btn = st.button("📑 Generate Report", type="primary", use_container_width=True)

    if generate_btn:
        if not company_name.strip():
            st.warning("Please provide a company name in the sidebar.")
        else:
            with st.spinner(f"Analyzing statements and risk factors for {company_name}..."):
                try:
                    report_content = generate_report(company_name, selected_pdf)
                    st.session_state[f"report_{company_name}"] = report_content
                except Exception as e:
                    st.error(f"Failed to generate report: {e}")

    # Display saved or newly generated report
    saved_report = st.session_state.get(f"report_{company_name}")
    if saved_report:
        st.divider()
        st.markdown(saved_report)
        st.download_button(
            label="📥 Download Report (.md)",
            data=saved_report,
            file_name=f"{company_name}_Financial_Report.md",
            mime="text/markdown",
            use_container_width=True
        )


# ---------------- TAB 2: CHATBOT ----------------
with tab_chat:
    st.subheader("💬 Interactive Financial Assistant")
    st.caption(f"Currently querying: **{company_name}**" + (f" (`{selected_pdf}`)" if selected_pdf else " (All documents)"))

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display clear chat button in an expander or header
    col_chat_title, col_chat_clear = st.columns([5, 1])
    with col_chat_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Display conversation messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle user query
    if user_query := st.chat_input("Ask a question (e.g., What was the net sales growth this fiscal year?)"):
        # Display user question
        st.chat_message("user").markdown(user_query)
        st.session_state.messages.append({"role": "user", "content": user_query})

        # Format history for backend API (excluding the current query)
        api_chat_history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]
        ]

        # Stream assistant response
        with st.chat_message("assistant"):
            response_generator = stream_chat_response(
                query=user_query,
                company_name=company_name,
                source_pdf=selected_pdf,
                chat_history=api_chat_history
            )
            full_response = st.write_stream(response_generator)

        st.session_state.messages.append({"role": "assistant", "content": full_response})