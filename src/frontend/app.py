import streamlit as st
import requests
import json
import os

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000/api/v1")

# Page Configuration
st.set_page_config(
    page_title="AI-Powered Financial Intelligence",
    page_icon="📊",
    layout="wide",          
    initial_sidebar_state="expanded"
)

# Premium Modern CSS Styling with Glassmorphism, Google Fonts, and Custom Metric Cards
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Container background subtle gradient */
    .stApp {
        background: linear-gradient(180deg, #FAFAFD 0%, #F1F4F9 100%);
    }

    /* Hero Banner Header with Glassmorphism */
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #1E3A8A 100%);
        border-radius: 20px;
        padding: 30px 36px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15), 0 8px 10px -6px rgba(15, 23, 42, 0.1);
        position: relative;
        overflow: hidden;
    }
    .hero-banner::after {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 350px;
        height: 350px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.25) 0%, rgba(255, 255, 255, 0) 70%);
        border-radius: 50%;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-top: 8px;
        font-weight: 400;
        max-width: 650px;
        line-height: 1.5;
    }
    .hero-badge {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        background: rgba(59, 130, 246, 0.25);
        color: #60A5FA;
        border: 1px solid rgba(96, 165, 250, 0.3);
        padding: 4px 10px;
        border-radius: 20px;
    }

    /* Quick Metric Cards */
    .stat-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
    }
    .stat-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .stat-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 4px;
    }

    /* Status Badges */
    .status-badge-ok {
        background-color: #ECFDF5;
        color: #047857;
        border: 1px solid #A7F3D0;
        padding: 5px 12px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .status-badge-err {
        background-color: #FEF2F2;
        color: #B91C1C;
        border: 1px solid #FECACA;
        padding: 5px 12px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* Sleek Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #E2E8F0;
        padding: 6px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        font-weight: 600;
        border-radius: 8px;
        color: #475569;
        background-color: transparent;
        padding: 0 20px;
        border: none;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #1E3A8A !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }

    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
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
    st.markdown("### ⚙️ System & Controls")
    
    # Backend Status Indicator
    is_healthy = check_backend_health()
    if is_healthy:
        st.markdown('<div class="status-badge-ok"><span>●</span> Backend Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge-err"><span>●</span> Backend Offline</div>', unsafe_allow_html=True)
        st.caption("Verify backend service is running on port 8000.")

    st.markdown("---")

    # Upload Section
    st.markdown("#### 📄 Ingest Report (10-K / Annual)")
    uploaded_file = st.file_uploader(
        "Upload SEC 10-K Filing or Annual PDF",
        type=["pdf"],
        help="Upload PDF reports to parse, chunk, and index into ChromaDB vector storage."
    )

    if uploaded_file is not None:
        if st.button("🚀 Upload & Index PDF", use_container_width=True):
            with st.spinner("Processing PDF chunks and computing vector embeddings..."):
                status_code, res = upload_pdf(uploaded_file)
                if status_code == 200:
                    st.success(f"Successfully indexed {res.get('chunks_indexed', 0)} chunks!")
                    st.rerun()
                else:
                    st.error(f"Upload failed: {res.get('detail', 'Unknown error')}")

    st.markdown("---")

    # Document Selection
    st.markdown("#### 🎯 Context & Target")
    available_files = get_available_companies()

    selected_pdf = st.selectbox(
        "Active SEC Filing",
        options=["None (Search All Documents)"] + available_files,
        index=1 if available_files else 0,
        help="Select a specific annual report or search across all ingested documents."
    )
    if selected_pdf == "None (Search All Documents)":
        selected_pdf = None

    default_company = ""
    if selected_pdf:
        # Infer company name from filename e.g. "NASDAQ_AAPL_2025.pdf" -> "AAPL"
        parts = selected_pdf.replace(".pdf", "").split("_")
        default_company = parts[1] if len(parts) > 1 else parts[0]

    company_name = st.text_input(
        "Target Company Name / Ticker",
        value=default_company or "Apple",
        help="Specify the target company name or ticker for grounded analysis."
    )

    st.markdown("---")
    st.caption("Powered by AWS Bedrock • LangChain • ChromaDB • FastAPI")


# ---------------- HERO HEADER ----------------
st.markdown(f"""
<div class="hero-banner">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
        <div>
            <div class="hero-title">
                📊 AI-Powered Financial Intelligence
                <span class="hero-badge">AWS EC2 Production</span>
            </div>
            <div class="hero-subtitle">
                Autonomous Deep RAG system parsing SEC 10-K filings, quarterly earnings, and balance sheets with institutional rigor.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------- QUICK METRIC CARDS ----------------
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Target Asset</div>
        <div class="stat-value">{company_name or "All"}</div>
    </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Active Document</div>
        <div class="stat-value" style="font-size: 1.05rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            {selected_pdf.split('/')[-1] if selected_pdf else "Global Vector Index"}
        </div>
    </div>
    """, unsafe_allow_html=True)
with m3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Indexed Filings</div>
        <div class="stat-value">{len(available_files)} Files</div>
    </div>
    """, unsafe_allow_html=True)
with m4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Retrieval Engine</div>
        <div class="stat-value" style="color: #2563EB;">Bedrock + Chroma</div>
    </div>
    """, unsafe_allow_html=True)

st.write("") # subtle spacing

# ---------------- MAIN TABS ----------------
tab_report, tab_chat = st.tabs(["📑 Institutional Report Generator", "💬 Conversational Analyst"])

# ---------------- TAB 1: FINANCIAL REPORT ----------------
with tab_report:
    st.markdown("### 📑 Institutional Financial Analysis Generator")
    st.write(
        f"Generate a multi-section financial dossier for **{company_name}**"
        + (f" grounded specifically in `{selected_pdf}`." if selected_pdf else " synthesized across all available filings.")
    )

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        generate_btn = st.button("⚡ Generate Complete Report", type="primary", use_container_width=True)

    if generate_btn:
        if not company_name.strip():
            st.warning("Please specify a company name or ticker in the sidebar.")
        else:
            with st.spinner(f"Synthesizing financial statements, operational risks, and key metrics for {company_name}..."):
                try:
                    report_content = generate_report(company_name, selected_pdf)
                    st.session_state[f"report_{company_name}"] = report_content
                except Exception as e:
                    st.error(f"Failed to generate report: {e}")

    # Display saved or newly generated report
    saved_report = st.session_state.get(f"report_{company_name}")
    if saved_report:
        st.markdown("---")
        st.markdown(saved_report)
        st.download_button(
            label="📥 Download Report as Markdown (.md)",
            data=saved_report,
            file_name=f"{company_name}_Financial_Report.md",
            mime="text/markdown",
            use_container_width=True
        )


# ---------------- TAB 2: CHATBOT ----------------
with tab_chat:
    c_title, c_clear = st.columns([5, 1])
    with c_title:
        st.markdown("### 💬 Conversational Financial Analyst")
        st.caption(f"Context: **{company_name}**" + (f" (`{selected_pdf}`)" if selected_pdf else " (Synthesizing across all indexed filings)"))
    with c_clear:
        if st.button("🗑️ Reset Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": f"Hello! I am your AI financial research assistant. Ask me anything about **{company_name}**'s revenue breakdown, risk factors, margins, or forward guidance."}
        ]

    # Display conversation messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle user query
    if user_query := st.chat_input("Ask a financial question (e.g., What are the primary risk factors mentioned in Item 1A?)"):
        st.chat_message("user").markdown(user_query)
        st.session_state.messages.append({"role": "user", "content": user_query})

        # Format history for backend API (excluding the current query)
        api_chat_history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[1:-1]
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