import React from 'react';
import { Layers, ShieldCheck, Database, FileSearch, Scale, Cpu, CheckCircle2 } from 'lucide-react';

export default function AboutView() {
  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800 text-center">
        <span className="text-xs font-semibold uppercase tracking-wider px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          SEPP · Course Research Track
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mt-3">
          GreenClaim AI — Architecture & Methodology
        </h2>
        <p className="text-sm text-slate-400 mt-2 max-w-2xl mx-auto leading-relaxed">
          An evidence-grounded greenwashing detection and analysis platform leveraging Retrieval-Augmented Generation (RAG) to cross-reference corporate sustainability claims against audited BRSR disclosures.
        </p>
      </div>

      {/* RAG vs Plain LLM Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel rounded-2xl p-6 border border-rose-500/20 bg-rose-950/5">
          <div className="flex items-center space-x-2 text-rose-400 font-bold text-sm mb-3">
            <span>❌ Plain LLM (Without Retrieval)</span>
          </div>
          <ul className="space-y-2 text-xs text-slate-300">
            <li className="flex items-start space-x-2">
              <span className="text-rose-400">•</span>
              <span>Can hallucinate corporate ESG metrics with high confidence.</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-rose-400">•</span>
              <span>Confuses "sounds right" with factual compliance.</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-rose-400">•</span>
              <span>No traceable evidence: outputs black-box opinions that cannot be verified in court or regulatory audits.</span>
            </li>
          </ul>
        </div>

        <div className="glass-panel rounded-2xl p-6 border border-emerald-500/20 bg-emerald-950/5">
          <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm mb-3">
            <span>✅ GreenClaim AI (RAG Pipeline)</span>
          </div>
          <ul className="space-y-2 text-xs text-slate-300">
            <li className="flex items-start space-x-2">
              <span className="text-emerald-400">•</span>
              <span>Grounds every verdict in statutory SEBI BRSR Principle 6 filings and GRI 305 standards.</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-emerald-400">•</span>
              <span>Extracts clean text page-by-page via PyMuPDF to cite exact document pages and snippets.</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-emerald-400">•</span>
              <span>Calculates a deterministic 5-factor risk score with Explainable AI reasoning.</span>
            </li>
          </ul>
        </div>
      </div>

      {/* 5-Factor Scoring Formulation */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800">
        <div className="flex items-center space-x-2 mb-4 pb-3 border-b border-slate-800">
          <Scale className="w-5 h-5 text-emerald-400" />
          <h3 className="text-base font-bold text-white">
            Greenwashing Risk Score Formulation (0–100)
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-emerald-400 font-mono font-bold text-lg">30%</div>
            <div className="text-xs font-semibold text-white mt-1">Evidence Strength</div>
            <p className="text-[11px] text-slate-400 mt-1">Degree to which retrieved statutory passages confirm the claim.</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-cyan-400 font-mono font-bold text-lg">20%</div>
            <div className="text-xs font-semibold text-white mt-1">Claim Specificity</div>
            <p className="text-[11px] text-slate-400 mt-1">Penalizes vague buzzwords (e.g. 100%, pure green) lacking baselines.</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-indigo-400 font-mono font-bold text-lg">20%</div>
            <div className="text-xs font-semibold text-white mt-1">Source Reliability</div>
            <p className="text-[11px] text-slate-400 mt-1">Audited statutory disclosures vs unaudited press releases.</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-rose-400 font-mono font-bold text-lg">20%</div>
            <div className="text-xs font-semibold text-white mt-1">Contradictory Data</div>
            <p className="text-[11px] text-slate-400 mt-1">Direct conflicts with reported emissions or heavy offset reliance.</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-amber-400 font-mono font-bold text-lg">10%</div>
            <div className="text-xs font-semibold text-white mt-1">Missing Baseline</div>
            <p className="text-[11px] text-slate-400 mt-1">Absence of Scope 3 boundaries or verification benchmarks.</p>
          </div>
        </div>

        {/* Bands */}
        <div className="mt-6 pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs">
          <span className="font-semibold text-slate-300">Interpretation Bands:</span>
          <span className="px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">0–25: Low Risk / Verified</span>
          <span className="px-2.5 py-1 rounded bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 font-mono">26–50: Moderate Risk / Partial</span>
          <span className="px-2.5 py-1 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20 font-mono">51–75: High Risk / Weak Evidence</span>
          <span className="px-2.5 py-1 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-mono">76–100: Very High / Greenwashing</span>
        </div>
      </div>
    </div>
  );
}
