import React, { useState, useEffect } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Building2, HardDrive, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function DocumentUploader({ companies }) {
  const [selectedCompanyId, setSelectedCompanyId] = useState(companies[0]?.id || 1);
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(true);

  // Set default company when companies prop arrives
  useEffect(() => {
    if (companies && companies.length > 0 && !selectedCompanyId) {
      setSelectedCompanyId(companies[0].id);
    }
  }, [companies, selectedCompanyId]);

  const fetchDocuments = async () => {
    setLoadingDocs(true);
    try {
      const docs = await api.getDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setUploadError('Only PDF files are supported for BRSR text extraction.');
        setFile(null);
        return;
      }
      setFile(selected);
      setUploadError(null);
      setUploadSuccess(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !selectedCompanyId) return;

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append('company_id', selectedCompanyId);
    formData.append('file', file);

    try {
      const res = await api.uploadDocument(formData);
      setUploadSuccess(`Extracted ${res.page_count} pages with PyMuPDF successfully!`);
      setFile(null);
      // Reset input
      const fileInput = document.getElementById('brsr-file-input');
      if (fileInput) fileInput.value = '';
      fetchDocuments();
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Failed to upload and process PDF.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 mb-6 border-b border-slate-800">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">Statutory Knowledge Ingestion</span>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-0.5">
              Upload Company BRSR & ESG Reports
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Ingest PDF disclosures directly into the RAG vector pipeline via PyMuPDF page-by-page text parser.
            </p>
          </div>
        </div>

        <form onSubmit={handleUpload} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
            {/* Company Selection */}
            <div className="md:col-span-5 space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
                <Building2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Target Entity for Filing</span>
              </label>
              <select
                value={selectedCompanyId}
                onChange={(e) => setSelectedCompanyId(e.target.value)}
                disabled={isUploading}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.sector})
                  </option>
                ))}
              </select>
            </div>

            {/* File Dropzone */}
            <div className="md:col-span-7 space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
                <FileText className="w-3.5 h-3.5 text-teal-400" />
                <span>Upload PDF Document</span>
              </label>
              <div className="relative border-2 border-dashed border-slate-700 hover:border-emerald-500/50 rounded-xl p-4 bg-slate-900/50 transition text-center cursor-pointer">
                <input
                  id="brsr-file-input"
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  disabled={isUploading}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="flex flex-col items-center justify-center space-y-1">
                  <UploadCloud className="w-6 h-6 text-emerald-400" />
                  <span className="text-xs font-medium text-slate-300">
                    {file ? file.name : 'Click or drag BRSR / ESG PDF here'}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'Supported: .pdf reports (up to 50MB)'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Feedback Alerts */}
          {uploadSuccess && (
            <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center space-x-2 text-xs text-emerald-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{uploadSuccess}</span>
            </div>
          )}

          {uploadError && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center space-x-2 text-xs text-rose-300">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {/* Submit Upload */}
          <button
            type="submit"
            disabled={isUploading || !file}
            className={`w-full py-3 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center justify-center space-x-2 transition ${
              isUploading || !file
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                : 'bg-emerald-600 hover:bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20'
            }`}
          >
            {isUploading ? (
              <span className="flex items-center space-x-2">
                <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                <span>Extracting Text with PyMuPDF...</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1.5">
                <UploadCloud className="w-4 h-4" />
                <span>Process & Index PDF Disclosures</span>
              </span>
            )}
          </button>
        </form>
      </div>

      {/* Indexed Document Library */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <HardDrive className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Ingested BRSR Disclosures ({documents.length})
            </h3>
          </div>
          <button
            onClick={fetchDocuments}
            className="text-slate-400 hover:text-white transition p-1"
            title="Refresh documents list"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingDocs ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {loadingDocs ? (
          <div className="py-6 text-center text-xs text-slate-400 font-mono">Loading document library...</div>
        ) : documents.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            No custom documents uploaded yet. Default statutory NSE knowledge base is currently active for all 15 entities.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between"
              >
                <div className="flex items-center space-x-2.5 min-w-0">
                  <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
                  <div className="truncate">
                    <span className="text-xs font-semibold text-white block truncate">{doc.file_name}</span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {doc.page_count} pages extracted
                    </span>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono shrink-0">
                  Indexed
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
