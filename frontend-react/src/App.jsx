import React, { useState, useEffect, useRef } from 'react';
import { 
  TrendingUp, 
  FileText, 
  MessageSquare, 
  UploadCloud, 
  Activity, 
  CheckCircle2, 
  AlertCircle, 
  Download, 
  Send, 
  Trash2, 
  Building2, 
  ShieldAlert, 
  BarChart3, 
  Sparkles,
  RefreshCw,
  Search
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function App() {
  // Application State
  const [backendHealthy, setBackendHealthy] = useState(false);
  const [companies, setCompanies] = useState([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [companyName, setCompanyName] = useState('Apple');
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'report' | 'chat'

  // Upload State
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  // Report State
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportData, setReportData] = useState('');
  const [reportError, setReportError] = useState('');

  // Chat State
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am AlphaPulse, your enterprise financial intelligence analyst. Ask any grounded question regarding balance sheets, liquidity, segment growth, or Item 1A operational risks.'
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef(null);

  // Poll Health & Available Files
  useEffect(() => {
    checkHealth();
    fetchCompanies();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      setBackendHealthy(res.ok);
    } catch {
      setBackendHealthy(false);
    }
  };

  const fetchCompanies = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/companies`);
      if (res.ok) {
        const data = await res.json();
        setCompanies(data.files || []);
        if (data.files?.length > 0 && !selectedFile) {
          setSelectedFile(data.files[0]);
          inferCompanyName(data.files[0]);
        }
      }
    } catch (err) {
      console.error('Error fetching companies:', err);
    }
  };

  const inferCompanyName = (filename) => {
    if (!filename) return;
    const clean = filename.replace('.pdf', '');
    const parts = clean.split('_');
    const name = parts.length > 1 ? parts[1] : parts[0];
    setCompanyName(name);
  };

  const handleFileChange = (e) => {
    const file = e.target.value;
    setSelectedFile(file);
    inferCompanyName(file);
  };

  // Upload PDF Handler
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setUploadStatus({ type: 'success', msg: `Indexed ${data.chunks_indexed} chunks into ChromaDB!` });
        fetchCompanies();
      } else {
        setUploadStatus({ type: 'error', msg: data.detail || 'Upload failed' });
      }
    } catch (err) {
      setUploadStatus({ type: 'error', msg: String(err) });
    } finally {
      setUploading(false);
    }
  };

  // Generate Institutional Report
  const handleGenerateReport = async () => {
    if (!companyName.trim()) return;
    setGeneratingReport(true);
    setReportError('');
    setActiveTab('report');

    try {
      const res = await fetch(`${API_BASE_URL}/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: companyName,
          source_pdf: selectedFile || null
        })
      });
      const data = await res.json();
      if (res.ok) {
        setReportData(data.report || 'No content generated.');
      } else {
        setReportError(data.detail || 'Failed to generate report');
      }
    } catch (err) {
      setReportError(String(err));
    } finally {
      setGeneratingReport(false);
    }
  };

  // Stream Chat Response
  const handleSendMessage = async (queryText) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || isStreaming) return;

    const userMsg = { role: 'user', content: textToSend };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInputQuery('');
    setIsStreaming(true);

    const apiHistory = newMessages.slice(1, -1).map(m => ({
      role: m.role,
      content: m.content
    }));

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: textToSend,
          company_name: companyName,
          source_pdf: selectedFile || null,
          chat_history: apiHistory,
          stream: true
        })
      });

      if (!res.ok) {
        const errorText = await res.text();
        setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ Error: ${errorText}` }]);
        setIsStreaming(false);
        return;
      }

      // Read SSE stream
      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let assistantResponse = '';

      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        assistantResponse += chunk;
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: 'assistant', content: assistantResponse };
          return updated;
        });
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ Network error: ${String(err)}` }]);
    } finally {
      setIsStreaming(false);
    }
  };

  const downloadReport = () => {
    const blob = new Blob([reportData], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${companyName}_Financial_Dossier.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="app-shell">
      {/* 1. TOP NAVBAR */}
      <header className="top-navbar">
        <div className="brand">
          <div className="brand-icon">
            <TrendingUp size={22} />
          </div>
          <span className="brand-name">AlphaPulse</span>
          <span className="brand-badge">Enterprise RAG</span>
        </div>

        {/* Live Market Tickers */}
        <div className="ticker-strip">
          <div className="ticker-item">
            <span className="ticker-symbol">AAPL</span>
            <span className="ticker-val">$242.10</span>
            <span className="ticker-change-pos">+1.42%</span>
          </div>
          <div className="ticker-item">
            <span className="ticker-symbol">MSFT</span>
            <span className="ticker-val">$428.50</span>
            <span className="ticker-change-pos">+0.88%</span>
          </div>
          <div className="ticker-item">
            <span className="ticker-symbol">NVDA</span>
            <span className="ticker-val">$135.20</span>
            <span className="ticker-change-neg">-0.45%</span>
          </div>
          <div className="ticker-item">
            <span className="ticker-symbol">AMZN</span>
            <span className="ticker-val">$194.80</span>
            <span className="ticker-change-pos">+2.15%</span>
          </div>
        </div>

        {/* System Status Indicator */}
        <div className={`system-status ${backendHealthy ? 'status-online' : 'status-offline'}`}>
          <div className="status-dot"></div>
          <span>{backendHealthy ? 'FastAPI & ChromaDB Live' : 'Backend Disconnected'}</span>
        </div>
      </header>

      {/* 2. MAIN LAYOUT */}
      <div className="main-layout">
        {/* LEFT SIDEBAR CONTROLS */}
        <aside className="sidebar">
          <div>
            <div className="section-title">
              <UploadCloud size={14} />
              <span>SEC Filing Ingestion</span>
            </div>
            <label className="upload-dropzone">
              <input 
                type="file" 
                accept=".pdf" 
                onChange={handleFileUpload} 
                style={{ display: 'none' }} 
                disabled={uploading}
              />
              <UploadCloud className="upload-icon" />
              <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                {uploading ? 'Chunking & Indexing...' : 'Upload Annual 10-K (PDF)'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Automated chunking + Titan Embeddings
              </div>
            </label>

            {uploadStatus && (
              <div style={{ 
                marginTop: '10px', 
                padding: '8px 12px', 
                borderRadius: '8px', 
                fontSize: '0.8rem',
                backgroundColor: uploadStatus.type === 'success' ? 'var(--accent-green-subtle)' : 'var(--accent-red-subtle)',
                color: uploadStatus.type === 'success' ? 'var(--accent-green)' : 'var(--accent-red)'
              }}>
                {uploadStatus.msg}
              </div>
            )}
          </div>

          <div>
            <div className="section-title">
              <Building2 size={14} />
              <span>Target & Context</span>
            </div>
            
            <div className="input-group" style={{ marginBottom: '14px' }}>
              <label className="input-label">Target Asset / Ticker</label>
              <input 
                type="text" 
                className="text-input" 
                value={companyName} 
                onChange={(e) => setCompanyName(e.target.value)} 
                placeholder="e.g. Apple, Tesla, AAPL"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Grounding Document</label>
              <select className="select-input" value={selectedFile} onChange={handleFileChange}>
                <option value="">All Ingested Reports ({companies.length})</option>
                {companies.map((file, idx) => (
                  <option key={idx} value={file}>{file}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
            <button 
              className="btn-primary" 
              style={{ width: '100%' }}
              onClick={handleGenerateReport}
              disabled={generatingReport}
            >
              <Sparkles size={16} />
              <span>{generatingReport ? 'Analyzing Statements...' : 'Synthesize Dossier'}</span>
            </button>
          </div>
        </aside>

        {/* WORKSPACE CENTER */}
        <main className="workspace">
          {/* Executive Metrics Grid */}
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-header">
                <span>Active Company</span>
                <Building2 size={16} />
              </div>
              <div className="metric-value">{companyName}</div>
              <div className="metric-sub">{selectedFile || 'Global Multi-Filing Index'}</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Indexed Filings</span>
                <FileText size={16} />
              </div>
              <div className="metric-value">{companies.length}</div>
              <div className="metric-sub">5,760+ Chunks in ChromaDB</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Inference Engine</span>
                <Activity size={16} color="var(--accent-blue)" />
              </div>
              <div className="metric-value" style={{ color: 'var(--accent-blue)' }}>AWS Bedrock</div>
              <div className="metric-sub">Nova-Pro / LLaMA-3.1 70B</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Architecture</span>
                <CheckCircle2 size={16} color="var(--accent-green)" />
              </div>
              <div className="metric-value" style={{ color: 'var(--accent-green)' }}>EC2 x86_64</div>
              <div className="metric-sub">Docker Microservices</div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="tab-nav">
            <button 
              className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              <BarChart3 size={16} />
              <span>Intelligence Overview</span>
            </button>
            <button 
              className={`tab-btn ${activeTab === 'report' ? 'active' : ''}`}
              onClick={() => setActiveTab('report')}
            >
              <FileText size={16} />
              <span>Institutional Dossier {reportData && '• Available'}</span>
            </button>
          </div>

          {/* Tab 1: Overview */}
          {activeTab === 'overview' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div className="report-container">
                <h3 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldAlert size={18} color="var(--accent-amber)" />
                  SEC Item 1A: Operational Risk Vector
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                  AlphaPulse autonomously retrieves and isolates core risk disclosures including supply chain concentration, foreign exchange headwinds, antitrust scrutiny, and capital expenditure exposure directly from audited 10-K submissions.
                </p>
                <div style={{ marginTop: '16px', display: 'flex', gap: '8px' }}>
                  <button 
                    className="btn-secondary"
                    onClick={() => handleSendMessage(`Analyze the top 3 regulatory and operational risks for ${companyName} from Item 1A.`)}
                  >
                    Query Risk Factors
                  </button>
                </div>
              </div>

              <div className="report-container">
                <h3 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BarChart3 size={18} color="var(--accent-green)" />
                  SEC Item 7: MD&A Financial Performance
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                  Synthesize management discussion, operating margin expansion/contraction, free cash flow generation, and forward-looking guidance without hallucination.
                </p>
                <div style={{ marginTop: '16px', display: 'flex', gap: '8px' }}>
                  <button 
                    className="btn-secondary"
                    onClick={() => handleSendMessage(`Summarize the revenue growth and operating margin trends for ${companyName} in the latest fiscal year.`)}
                  >
                    Query Operating Margins
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Institutional Report */}
          {activeTab === 'report' && (
            <div className="report-container">
              <div className="report-header">
                <div>
                  <h2>Institutional Financial Report: {companyName}</h2>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '4px' }}>
                    Grounded in: {selectedFile || 'All Indexed Reports'}
                  </div>
                </div>
                {reportData && (
                  <button className="btn-secondary" onClick={downloadReport}>
                    <Download size={16} />
                    <span>Export Dossier (.md)</span>
                  </button>
                )}
              </div>

              {generatingReport ? (
                <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
                  <RefreshCw size={36} className="spin" style={{ animation: 'spin 1s linear infinite', margin: '0 auto 16px', color: 'var(--accent-blue)' }} />
                  <div style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--text-primary)' }}>Synthesizing Institutional Dossier...</div>
                  <div style={{ fontSize: '0.9rem', marginTop: '6px' }}>Retrieving Balance Sheets, MD&A, and Item 1A disclosures</div>
                </div>
              ) : reportError ? (
                <div style={{ padding: '20px', borderRadius: '12px', background: 'var(--accent-red-subtle)', color: 'var(--accent-red)' }}>
                  {reportError}
                </div>
              ) : reportData ? (
                <div className="report-body">
                  {reportData}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                  <FileText size={48} style={{ margin: '0 auto 16px', opacity: 0.4 }} />
                  <div style={{ fontSize: '1rem', fontWeight: 600 }}>No Dossier Generated Yet</div>
                  <p style={{ fontSize: '0.85rem', marginTop: '6px' }}>Click "Synthesize Dossier" in the left sidebar to generate a comprehensive institutional analysis.</p>
                </div>
              )}
            </div>
          )}
        </main>

        {/* RIGHT DOCKED AI ANALYST CHAT DRAWER */}
        <aside className="chat-drawer">
          <div className="chat-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MessageSquare size={18} color="var(--accent-blue)" />
              <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>AI Financial Analyst</span>
            </div>
            <button 
              className="btn-secondary" 
              style={{ padding: '4px 8px', fontSize: '0.75rem' }}
              onClick={() => setMessages([{ role: 'assistant', content: 'Conversation reset. How can I assist your financial analysis?' }])}
            >
              <Trash2 size={13} />
            </button>
          </div>

          {/* Quick Prompt Chips */}
          <div className="chips-container" style={{ paddingTop: '10px' }}>
            <div className="chip" onClick={() => handleSendMessage('Break down revenue by product line.')}>
              Revenue breakdown
            </div>
            <div className="chip" onClick={() => handleSendMessage('What are the primary operational risks?')}>
              Risk factors
            </div>
            <div className="chip" onClick={() => handleSendMessage('Analyze cash flow and liquidity.')}>
              Liquidity & Cash
            </div>
          </div>

          {/* Message List */}
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={`chat-msg ${msg.role === 'user' ? 'chat-msg-user' : 'chat-msg-assistant'}`}
              >
                {msg.content}
              </div>
            ))}
            {isStreaming && (
              <div style={{ fontSize: '0.8rem', color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="spin">●</span> AlphaPulse is generating tokens...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input */}
          <form 
            className="chat-input-area"
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
          >
            <input 
              type="text" 
              className="chat-input"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder={`Ask about ${companyName}...`}
              disabled={isStreaming}
            />
            <button 
              type="submit" 
              className="btn-primary" 
              style={{ padding: '10px 14px' }}
              disabled={isStreaming || !inputQuery.trim()}
            >
              <Send size={16} />
            </button>
          </form>
        </aside>
      </div>
    </div>
  );
}
