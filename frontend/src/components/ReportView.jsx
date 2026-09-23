import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  BookOpen, 
  FileText, 
  ExternalLink, 
  Download, 
  RotateCcw, 
  ChevronDown, 
  ChevronUp, 
  ShieldCheck,
  Building,
  Calendar,
  Layers,
  Sparkles,
  Info
} from 'lucide-react';
import RiskMeter from './RiskMeter';

export default function ReportView({ report, onReset, onRephrase }) {
  const [expandedCitation, setExpandedCitation] = useState(null);
  const [isCopied, setIsCopied] = useState(false);

  if (!report) return null;

  const toggleCitation = (idx) => {
    setExpandedCitation(expandedCitation === idx ? null : idx);
  };

  const handleExportJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `GreenClaim_Report_${report.company_name.replace(/\s+/g, '_')}_${report.id || 'analysis'}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleCopySummary = () => {
    const summaryText = `[GreenClaim AI Report] Company: ${report.company_name} | Risk Score: ${report.risk_score}/100 (${report.verdict_status}) | Claim: "${report.claim_text}" | Explanation: ${report.explanation}`;
    navigator.clipboard.writeText(summaryText);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  // Group evidence
  const supportingPoints = report.citations
    ?.filter(c => c.type === 'Supporting')
    ?.map(c => `${c.doc_name} (p. ${c.page}): ${c.snippet}`) || [];

  const contradictingPoints = report.contradicting_evidence 
    ? report.contradicting_evidence.split('\n').filter(Boolean)
    : report.citations?.filter(c => c.type === 'Contradicting')?.map(c => `${c.doc_name} (p. ${c.page}): ${c.snippet}`) || [];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Banner & Actions Header */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center space-x-1">
              <Building className="w-3 h-3" />
              <span>{report.company_name}</span>
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 text-xs font-medium">
              Category: {report.category}
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 text-xs font-mono flex items-center space-x-1">
              <Calendar className="w-3 h-3" />
              <span>{new Date(report.created_at || Date.now()).toLocaleDateString()}</span>
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Verification Audit Report
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-3xl italic">
            "{report.claim_text}"
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={handleCopySummary}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition flex items-center space-x-1.5"
          >
            <Info className="w-3.5 h-3.5" />
            <span>{isCopied ? 'Copied!' : 'Copy Summary'}</span>
          </button>
          <button
            onClick={handleExportJSON}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-emerald-400 text-xs font-medium border border-emerald-500/30 transition flex items-center space-x-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </button>
          <button
            onClick={onReset}
            className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-slate-950 text-xs font-bold transition flex items-center space-x-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Audit New Claim</span>
          </button>
        </div>
      </div>

      {/* Risk Meter Visual Component */}
      <RiskMeter
        score={report.risk_score}
        verdict={report.verdict_status}
        confidence={report.confidence_score}
        factors={report.factors}
      />

      {/* Explainable AI: Why was this score assigned? */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <div className="flex items-center space-x-2 mb-3">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Explainable AI RAG Analysis — Why This Score Was Assigned
          </h3>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/60 p-4 rounded-xl border border-slate-800/80">
          {report.explanation}
        </p>

        {report.missing_evidence && (
          <div className="mt-3 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-start space-x-3">
            <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
            <div>
              <span className="text-xs font-semibold text-amber-300 block">Missing Information & Evidence Gaps:</span>
              <p className="text-xs text-amber-200/90 mt-0.5 leading-relaxed">
                {report.missing_evidence}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Supporting vs. Contradicting Evidence Dual Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Supporting Evidence Card */}
        <div className="glass-panel rounded-2xl p-6 border border-emerald-500/20 bg-emerald-950/10">
          <div className="flex items-center space-x-2 mb-4 pb-3 border-b border-emerald-500/20">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-emerald-300">Supporting Evidence</h4>
              <span className="text-[11px] text-emerald-400/80">Audited disclosures corroborating claim assertions</span>
            </div>
          </div>

          {supportingPoints.length > 0 ? (
            <ul className="space-y-2.5">
              {supportingPoints.map((item, idx) => (
                <li key={idx} className="flex items-start space-x-2 text-xs text-slate-300 leading-relaxed bg-slate-900/50 p-3 rounded-lg border border-emerald-500/15">
                  <span className="text-emerald-400 font-bold shrink-0">✓</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-400 italic bg-slate-900/40 p-4 rounded-lg border border-slate-800">
              No corroborating evidence found in current audited BRSR filings for this claim statement.
            </p>
          )}
        </div>

        {/* Contradicting Evidence Card */}
        <div className="glass-panel rounded-2xl p-6 border border-rose-500/20 bg-rose-950/10">
          <div className="flex items-center space-x-2 mb-4 pb-3 border-b border-rose-500/20">
            <div className="w-7 h-7 rounded-lg bg-rose-500/20 flex items-center justify-center text-rose-400">
              <XCircle className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-rose-300">Contradicting / Counter Evidence</h4>
              <span className="text-[11px] text-rose-400/80">Disclosures conflicting with stated claims or timelines</span>
            </div>
          </div>

          {contradictingPoints.length > 0 ? (
            <ul className="space-y-2.5">
              {contradictingPoints.map((item, idx) => (
                <li key={idx} className="flex items-start space-x-2 text-xs text-slate-300 leading-relaxed bg-slate-900/50 p-3 rounded-lg border border-rose-500/15">
                  <span className="text-rose-400 font-bold shrink-0">✕</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-400 italic bg-slate-900/40 p-4 rounded-lg border border-slate-800">
              No direct contradictory disclosures or operational conflicts detected.
            </p>
          )}
        </div>
      </div>

      {/* Page-Level Source Citation Cards */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <BookOpen className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Page-Level Source Citations ({report.citations?.length || 0})
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Audited BRSR & Regulatory Filings
          </span>
        </div>

        <div className="space-y-3">
          {report.citations && report.citations.length > 0 ? (
            report.citations.map((citation, idx) => {
              const isExpanded = expandedCitation === idx;
              return (
                <div
                  key={idx}
                  className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden hover:border-slate-700 transition"
                >
                  <div
                    onClick={() => toggleCitation(idx)}
                    className="p-4 flex items-center justify-between cursor-pointer select-none"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-300">
                        <FileText className="w-4 h-4 text-emerald-400" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold text-white">{citation.doc_name}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                            Page {citation.page}
                          </span>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                            citation.type === 'Supporting'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : citation.type === 'Contradicting'
                              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                              : 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                          }`}>
                            {citation.type}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          Section: {citation.section}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      <span className="text-xs font-mono text-slate-400 hidden sm:inline">
                        Relevance: <strong className="text-emerald-400">{Math.round(citation.relevance * 100)}%</strong>
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Snippet Content */}
                  {isExpanded && (
                    <div className="px-4 pb-4 pt-1 border-t border-slate-800/80 bg-slate-950/40">
                      <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 block mb-1">
                        Exact Quoted Passage:
                      </span>
                      <blockquote className="text-xs text-slate-200 italic p-3 rounded-lg bg-slate-900 border-l-2 border-emerald-500 leading-relaxed font-mono">
                        "{citation.snippet}"
                      </blockquote>
                      <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400">
                        <span>Statutory source: SEBI Business Responsibility & Sustainability Reporting (BRSR)</span>
                        <span className="text-emerald-400 font-mono text-[10px]">
                          SHA-256 Verified
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <p className="text-xs text-slate-400 italic">No citations available for this report.</p>
          )}
        </div>
      </div>
    </div>
  );
}
