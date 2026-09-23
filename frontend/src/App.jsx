import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ClaimForm from './components/ClaimForm';
import ReportView from './components/ReportView';
import ClaimHistory from './components/ClaimHistory';
import DocumentUploader from './components/DocumentUploader';
import AboutView from './components/AboutView';
import { api } from './services/api';
import { ShieldCheck, AlertCircle, Database, Leaf } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('verify');
  const [companies, setCompanies] = useState([]);
  const [activeReport, setActiveReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [backendStatus, setBackendStatus] = useState('connecting');

  // Load companies and check backend health on mount
  useEffect(() => {
    const initApp = async () => {
      try {
        const health = await api.checkHealth();
        if (health.status === 'healthy') {
          setBackendStatus('healthy');
        } else {
          setBackendStatus('offline');
        }

        const companyList = await api.getCompanies();
        setCompanies(companyList);
      } catch (err) {
        console.error('Initialization error:', err);
        setBackendStatus('offline');
        setApiError('Unable to connect to GreenClaim AI backend on http://localhost:8000. Ensure the FastAPI server is running.');
      }
    };

    initApp();
  }, []);

  const handleAnalyzeClaim = async (payload) => {
    setIsLoading(true);
    setApiError(null);
    try {
      const result = await api.analyzeClaim(payload);
      setActiveReport(result);
    } catch (err) {
      console.error('Analysis error:', err);
      setApiError(err.response?.data?.detail || 'Verification analysis failed. Please verify backend connection.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectHistoricalClaim = async (id) => {
    setIsLoading(true);
    setApiError(null);
    try {
      const details = await api.getClaimDetails(id);
      setActiveReport(details);
      setActiveTab('verify');
    } catch (err) {
      console.error('Failed to load historical claim:', err);
      setApiError('Failed to fetch historical audit report.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetReport = () => {
    setActiveReport(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500 selection:text-slate-950">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          setApiError(null);
        }}
        backendStatus={backendStatus}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Backend Warning Banner if offline */}
        {backendStatus === 'offline' && (
          <div className="mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start space-x-3 text-xs text-amber-200">
            <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
            <div>
              <strong className="text-amber-300 font-semibold block">Backend Disconnected</strong>
              <span>
                Could not connect to FastAPI at <code className="font-mono text-amber-400">http://localhost:8000/api/v1</code>.
                Make sure you run the backend using <code className="font-mono text-amber-300">uvicorn backend.app.main:app --reload</code>.
              </span>
            </div>
          </div>
        )}

        {/* Global Error Banner */}
        {apiError && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between text-xs text-rose-200">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{apiError}</span>
            </div>
            <button
              onClick={() => setApiError(null)}
              className="text-rose-400 hover:text-white font-bold ml-4"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Tab 1: Verify Claim */}
        {activeTab === 'verify' && (
          <div className="space-y-8">
            {activeReport ? (
              <ReportView
                report={activeReport}
                onReset={handleResetReport}
              />
            ) : (
              <ClaimForm
                companies={companies}
                onAnalyze={handleAnalyzeClaim}
                isLoading={isLoading}
              />
            )}
          </div>
        )}

        {/* Tab 2: Analysis History */}
        {activeTab === 'history' && (
          <ClaimHistory
            companies={companies}
            onSelectClaim={handleSelectHistoricalClaim}
          />
        )}

        {/* Tab 3: BRSR Document Upload */}
        {activeTab === 'upload' && (
          <DocumentUploader
            companies={companies}
          />
        )}

        {/* Tab 4: Methodology & IEEE Architecture */}
        {activeTab === 'about' && (
          <AboutView />
        )}
      </main>

      {/* Footer */}
      <footer className="glass-panel border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Leaf className="w-4 h-4 text-emerald-500" />
            <span className="font-semibold text-slate-400">GreenClaim AI Platform</span>
            <span>—</span>
            <span>Evidence-Grounded RAG System</span>
          </div>
          <div className="flex items-center space-x-4 font-mono text-[11px] text-slate-400">
            <span>SEBI BRSR FY 2025–26</span>
            <span>•</span>
            <span>GRI 305 Standards</span>
            <span>•</span>
            <span>PyMuPDF Engine</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
