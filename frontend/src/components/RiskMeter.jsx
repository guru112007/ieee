import React from 'react';
import { AlertTriangle, CheckCircle, HelpCircle, ShieldAlert, Sparkles } from 'lucide-react';

export default function RiskMeter({ score = 0, verdict = 'Verified', confidence = 0.9, factors = null }) {
  // Determine color theme based on score thresholds
  const getTheme = (val) => {
    if (val <= 25) {
      return {
        label: 'Low Risk — Verified',
        badgeBg: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
        strokeColor: '#10b981',
        glowClass: 'shadow-glow-green',
        icon: CheckCircle,
        desc: 'Claim is well-grounded in audited statutory BRSR filings with quantitative metrics.'
      };
    } else if (val <= 50) {
      return {
        label: 'Moderate Risk — Partially Supported',
        badgeBg: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
        strokeColor: '#eab308',
        glowClass: 'shadow-[0_0_25px_-5px_rgba(234,179,8,0.25)]',
        icon: HelpCircle,
        desc: 'Partial support exists but claim conflates targets or omits circular lifecycle steps.'
      };
    } else if (val <= 75) {
      return {
        label: 'High Risk — Weak / Unsupported',
        badgeBg: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
        strokeColor: '#f97316',
        glowClass: 'shadow-[0_0_25px_-5px_rgba(249,115,22,0.25)]',
        icon: AlertTriangle,
        desc: 'Weak supporting disclosures; substantial ambiguity or missing boundary parameters.'
      };
    } else {
      return {
        label: 'Very High Risk — Greenwashing',
        badgeBg: 'bg-red-500/15 text-red-400 border-red-500/30',
        strokeColor: '#ef4444',
        glowClass: 'shadow-glow-red',
        icon: ShieldAlert,
        desc: 'Claim directly conflicts with company BRSR disclosures or relies on deceptive framing.'
      };
    }
  };

  const theme = getTheme(score);
  const Icon = theme.icon;

  // Semicircle gauge calculation
  // Radius = 80, Circumference = 2 * PI * 80 = 502.65 -> Semicircle = 251.3
  const radius = 80;
  const circumference = Math.PI * radius; // ~251.3
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className={`glass-panel rounded-2xl p-6 border ${theme.glowClass} transition-all duration-300`}>
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">RAG Verification Engine</span>
          <h3 className="text-lg font-bold text-white">Greenwashing Risk Meter</h3>
        </div>
        <div className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${theme.badgeBg}`}>
          <Icon className="w-3.5 h-3.5" />
          <span>{verdict || theme.label}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* Gauge Visual */}
        <div className="md:col-span-5 flex flex-col items-center justify-center">
          <div className="relative w-48 h-28 flex items-end justify-center overflow-visible">
            <svg className="w-48 h-48 -rotate-180 transform" viewBox="0 0 200 200">
              {/* Background Arc */}
              <circle
                cx="100"
                cy="100"
                r={radius}
                fill="none"
                stroke="#1e293b"
                strokeWidth="16"
                strokeDasharray={`${circumference} ${circumference}`}
                strokeDashoffset="0"
                strokeLinecap="round"
              />
              {/* Progress Arc */}
              <circle
                cx="100"
                cy="100"
                r={radius}
                fill="none"
                stroke={theme.strokeColor}
                strokeWidth="16"
                strokeDasharray={`${circumference} ${circumference}`}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                style={{ transition: 'stroke-dashoffset 0.8s ease-out, stroke 0.4s ease' }}
              />
            </svg>

            {/* Score in Center */}
            <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
              <span className="text-4xl font-extrabold tracking-tight text-white font-mono">
                {score}
              </span>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest">
                Risk Index (0-100)
              </span>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between w-full max-w-[200px] text-[10px] text-slate-400 font-mono">
            <span className="text-emerald-400">0 (Safe)</span>
            <span className="text-yellow-400">50</span>
            <span className="text-red-400">100 (High Risk)</span>
          </div>

          <div className="mt-3 text-center">
            <span className="inline-block px-2.5 py-0.5 rounded-full bg-slate-800 text-[11px] font-medium text-slate-300">
              Confidence: <strong className="text-emerald-400">{Math.round(confidence * 100)}%</strong>
            </span>
          </div>
        </div>

        {/* 5-Factor Weighted Dimension Progress Bars */}
        <div className="md:col-span-7 space-y-3 pl-0 md:pl-4 md:border-l border-slate-800">
          <div className="text-xs font-semibold text-slate-300 mb-1 flex items-center justify-between">
            <span>IEEE SEPP Factor Matrix</span>
            <span className="text-[10px] text-slate-500 font-mono">Calibrated Weights</span>
          </div>

          {factors ? (
            <div className="space-y-2.5">
              {/* Evidence Strength (30%) */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-300 font-medium">Evidence Alignment (30%)</span>
                  <span className="text-slate-400 font-mono">{factors.evidence_strength}/100</span>
                </div>
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                    style={{ width: `${factors.evidence_strength}%` }}
                  />
                </div>
              </div>

              {/* Claim Specificity (20%) */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-300 font-medium">Vagueness / Specificity (20%)</span>
                  <span className="text-slate-400 font-mono">{factors.claim_specificity}/100</span>
                </div>
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-cyan-500 rounded-full transition-all duration-500"
                    style={{ width: `${factors.claim_specificity}%` }}
                  />
                </div>
              </div>

              {/* Source Reliability (20%) */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-300 font-medium">Source Reliability Risk (20%)</span>
                  <span className="text-slate-400 font-mono">{factors.source_reliability}/100</span>
                </div>
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                    style={{ width: `${factors.source_reliability}%` }}
                  />
                </div>
              </div>

              {/* Contradictory Evidence (20%) */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-300 font-medium">Contradictory Evidence (20%)</span>
                  <span className="text-slate-400 font-mono">{factors.contradictory_evidence}/100</span>
                </div>
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-rose-500 rounded-full transition-all duration-500"
                    style={{ width: `${factors.contradictory_evidence}%` }}
                  />
                </div>
              </div>

              {/* Missing Information (10%) */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-300 font-medium">Missing Baseline / Scope 3 (10%)</span>
                  <span className="text-slate-400 font-mono">{factors.missing_information}/100</span>
                </div>
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-amber-500 rounded-full transition-all duration-500"
                    style={{ width: `${factors.missing_information}%` }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">Factor metrics loaded from RAG pipeline.</p>
          )}

          <p className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/60 leading-relaxed">
            {theme.desc}
          </p>
        </div>
      </div>
    </div>
  );
}
