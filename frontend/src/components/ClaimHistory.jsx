import React, { useState, useEffect } from 'react';
import { History, Building2, Filter, Eye, ArrowRight, ShieldCheck, AlertTriangle, ShieldAlert, Sparkles, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function ClaimHistory({ onSelectClaim, companies }) {
  const [history, setHistory] = useState([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const fetchHistory = async () => {
    setIsLoading(true);
    try {
      const params = {};
      if (selectedCompanyId) params.company_id = selectedCompanyId;
      if (selectedCategory && selectedCategory !== 'All') params.category = selectedCategory;
      const data = await api.getClaimHistory(params);
      setHistory(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [selectedCompanyId, selectedCategory]);

  const getVerdictBadge = (status, score) => {
    if (score <= 25) {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1">
          <ShieldCheck className="w-3 h-3" />
          <span>Verified ({score})</span>
        </span>
      );
    } else if (score <= 50) {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-500/15 text-yellow-400 border border-yellow-500/30 flex items-center space-x-1">
          <AlertTriangle className="w-3 h-3" />
          <span>Partially Supported ({score})</span>
        </span>
      );
    } else if (score <= 75) {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-500/15 text-orange-400 border border-orange-500/30 flex items-center space-x-1">
          <AlertTriangle className="w-3 h-3" />
          <span>Weak Evidence ({score})</span>
        </span>
      );
    } else {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/15 text-red-400 border border-red-500/30 flex items-center space-x-1">
          <ShieldAlert className="w-3 h-3" />
          <span>High Risk ({score})</span>
        </span>
      );
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-800">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">Audit Trail</span>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-0.5">
            Claim Verification History
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Browse and inspect past evidence-grounded greenwashing assessments.
          </p>
        </div>

        {/* Refresh & Count */}
        <div className="flex items-center space-x-3">
          <span className="text-xs text-slate-400 font-mono">
            {history.length} audit records
          </span>
          <button
            onClick={fetchHistory}
            disabled={isLoading}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Refresh history"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-emerald-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center space-x-1.5">
            <Building2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Filter by Monitored Company</span>
          </label>
          <select
            value={selectedCompanyId}
            onChange={(e) => setSelectedCompanyId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">All Monitored Companies (15 NSE Entities)</option>
            {companies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.sector})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center space-x-1.5">
            <Filter className="w-3.5 h-3.5 text-teal-400" />
            <span>Filter by Claim Category</span>
          </label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">All Categories</option>
            <option value="Climate">Climate & Carbon</option>
            <option value="Waste">Waste & Packaging</option>
            <option value="Energy">Renewable Energy</option>
            <option value="Water">Water Stewardship</option>
            <option value="Product">Product & Materials</option>
          </select>
        </div>
      </div>

      {/* History Items List */}
      {isLoading ? (
        <div className="py-12 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-slate-400 font-mono">Loading audit history from database...</span>
        </div>
      ) : history.length === 0 ? (
        <div className="py-12 text-center bg-slate-900/40 rounded-xl border border-slate-800">
          <History className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-400 font-medium">No claim verification records found matching criteria.</p>
          <p className="text-xs text-slate-500 mt-1">Audit a new claim from the verification tab to start tracking.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <div
              key={item.id}
              className="p-4 sm:p-5 rounded-xl bg-slate-900/70 border border-slate-800/90 hover:border-slate-700 transition flex flex-col md:flex-row md:items-center justify-between gap-4 group"
            >
              <div className="space-y-1.5 flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-bold text-sm text-white">{item.company_name}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                    {item.category}
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono">
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-slate-300 font-mono line-clamp-2">
                  "{item.claim_text}"
                </p>
                <p className="text-[11px] text-slate-400 line-clamp-1 italic">
                  {item.explanation}
                </p>
              </div>

              <div className="flex items-center justify-between md:justify-end space-x-3 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-slate-800/60">
                <div>{getVerdictBadge(item.verdict_status, item.risk_score)}</div>
                <button
                  onClick={() => onSelectClaim(item.id)}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 group-hover:bg-emerald-600 group-hover:text-slate-950 text-slate-300 text-xs font-semibold border border-slate-700 group-hover:border-emerald-500 transition flex items-center space-x-1.5"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect Audit</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
