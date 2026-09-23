import React, { useState } from 'react';
import { 
  Sparkles, 
  Building2, 
  Tag, 
  FileUp, 
  HelpCircle, 
  ArrowRight, 
  CheckCircle2, 
  CloudRain, 
  Zap, 
  Recycle, 
  Globe, 
  Package,
  Layers
} from 'lucide-react';

const CATEGORIES = [
  { id: 'Climate', label: 'Climate & Carbon', icon: Globe, desc: 'Carbon neutral, Net Zero, Scope 1-3' },
  { id: 'Waste', label: 'Waste & Packaging', icon: Recycle, desc: '100% recyclable, zero landfill, plastic neutral' },
  { id: 'Energy', label: 'Renewable Energy', icon: Zap, desc: 'Clean power, solar transitions, green grids' },
  { id: 'Water', label: 'Water Stewardship', icon: CloudRain, desc: 'Water positive, circular recycling' },
  { id: 'Product', label: 'Product & Materials', icon: Package, desc: 'Eco-friendly, biodegradable, sustainable materials' },
];

const BENCHMARK_PRESETS = [
  {
    title: 'Tata Steel (Case Study — High Risk)',
    company: 'Tata Steel',
    category: 'Climate',
    claim: 'Already carbon-neutral with near-zero Scope 1 emissions across our steel manufacturing facilities.',
    badge: 'Expected: High Risk / Unsupported'
  },
  {
    title: 'Tata Steel (Case Study — Verified)',
    company: 'Tata Steel',
    category: 'Climate',
    claim: 'Has committed to net-zero operations by 2045 with capital allocation for scrap-based EAF transitions.',
    badge: 'Expected: Verified'
  },
  {
    title: 'Hindustan Unilever (Packaging)',
    company: 'Hindustan Unilever',
    category: 'Waste',
    claim: '100% of our plastic packaging is recyclable and plastic-neutral nationwide.',
    badge: 'Expected: Partially Supported'
  },
  {
    title: 'NTPC (Clean Power Claim)',
    company: 'NTPC Limited',
    category: 'Energy',
    claim: 'Zero-emission power producer leading India\'s clean energy transition.',
    badge: 'Expected: Unsupported / High Risk'
  }
];

export default function ClaimForm({ companies, onAnalyze, isLoading }) {
  const [selectedCompanyId, setSelectedCompanyId] = useState(companies[0]?.id || 1);
  const [selectedCategory, setSelectedCategory] = useState('Climate');
  const [claimText, setClaimText] = useState('');
  const [loadingStep, setLoadingStep] = useState(0);

  // Set default company when companies load
  React.useEffect(() => {
    if (companies && companies.length > 0 && !selectedCompanyId) {
      setSelectedCompanyId(companies[0].id);
    }
  }, [companies, selectedCompanyId]);

  // Loading animation message stepper
  React.useEffect(() => {
    let interval;
    if (isLoading) {
      setLoadingStep(0);
      interval = setInterval(() => {
        setLoadingStep((prev) => (prev < 3 ? prev + 1 : prev));
      }, 700);
    } else {
      setLoadingStep(0);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  const loadingMessages = [
    'Retrieving company BRSR statutory disclosures...',
    'Matching claim against GRI 305 & GHG Protocol boundaries...',
    'Evaluating contradictory emissions & offset reliance...',
    'Synthesizing Explainable AI verdict report...'
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!claimText.trim()) return;
    onAnalyze({
      company_id: parseInt(selectedCompanyId, 10),
      claim_text: claimText.trim(),
      category: selectedCategory,
    });
  };

  const handleApplyPreset = (preset) => {
    const matched = companies.find((c) => c.name.toLowerCase().includes(preset.company.toLowerCase()));
    if (matched) {
      setSelectedCompanyId(matched.id);
    }
    setSelectedCategory(preset.category);
    setClaimText(preset.claim);
  };

  const selectedCompanyObj = companies.find((c) => c.id === parseInt(selectedCompanyId, 10));

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-5 border-b border-slate-800">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">Claim Verification Portal</span>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-0.5">
            Audit Environmental Claim
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Ground statements in statutory BRSR filings, SEBI Principle 6 data, and global standards.
          </p>
        </div>

        {/* Quick Case Study Selector */}
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 font-medium hidden md:inline">Quick Case Studies:</span>
          <div className="flex flex-wrap gap-1.5">
            {BENCHMARK_PRESETS.slice(0, 2).map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleApplyPreset(preset)}
                className="text-[11px] font-medium px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/80 transition"
              >
                {preset.title.split('(')[0]} ({idx === 0 ? 'High Risk' : 'Verified'})
              </button>
            ))}
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Company & Category Selectors Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
          {/* Company Dropdown */}
          <div className="md:col-span-6 space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
              <Building2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Target Corporate Entity (NSE Listed)</span>
            </label>
            <div className="relative">
              <select
                value={selectedCompanyId}
                onChange={(e) => setSelectedCompanyId(e.target.value)}
                disabled={isLoading}
                className="w-full bg-slate-900 border border-slate-700/90 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition appearance-none cursor-pointer"
              >
                {companies.map((company) => (
                  <option key={company.id} value={company.id} className="bg-slate-900 text-white">
                    {company.name} ({company.sector}) {company.ticker ? `— [${company.ticker}]` : ''}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400">
                ▼
              </div>
            </div>
            {selectedCompanyObj && (
              <div className="flex items-center space-x-2 pt-1">
                <span className="text-[11px] text-slate-400">Sector:</span>
                <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-emerald-300 border border-slate-700">
                  {selectedCompanyObj.sector}
                </span>
                {selectedCompanyObj.description && (
                  <span className="text-[11px] text-slate-400 truncate max-w-[260px] hidden sm:inline">
                    {selectedCompanyObj.description}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Category Chips */}
          <div className="md:col-span-6 space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
              <Tag className="w-3.5 h-3.5 text-teal-400" />
              <span>Claim Domain Category</span>
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {CATEGORIES.map((cat) => {
                const Icon = cat.icon;
                const isSelected = selectedCategory === cat.id;
                return (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => setSelectedCategory(cat.id)}
                    className={`flex items-center space-x-2 p-2 rounded-xl text-left border transition ${
                      isSelected
                        ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-sm'
                        : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-emerald-400' : 'text-slate-500'}`} />
                    <span className="text-xs font-medium truncate">{cat.label.split('&')[0]}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Claim Input Area */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              <span>Public Environmental Claim or Marketing Statement</span>
            </label>
            <span className="text-[11px] text-slate-400">
              {claimText.length} characters
            </span>
          </div>

          <textarea
            rows={3}
            value={claimText}
            onChange={(e) => setClaimText(e.target.value)}
            disabled={isLoading}
            placeholder="e.g., 'We have achieved 100% carbon-neutral operations with zero Scope 1 emissions in our manufacturing facilities.'"
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition leading-relaxed"
          />
        </div>

        {/* Preset Carousel / Buttons */}
        <div className="pt-1">
          <span className="text-xs text-slate-400 font-medium block mb-2">Preset Benchmark Claims (Slide 10 & SEPP Test Cases):</span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {BENCHMARK_PRESETS.map((preset, idx) => (
              <div
                key={idx}
                onClick={() => handleApplyPreset(preset)}
                className="cursor-pointer p-2.5 rounded-xl bg-slate-900/50 hover:bg-slate-850 border border-slate-800/80 hover:border-emerald-500/40 transition group"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-slate-300 group-hover:text-emerald-400 transition">
                    {preset.title}
                  </span>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono ${
                    preset.badge.includes('Verified') 
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                      : preset.badge.includes('Partially')
                      ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                      : 'bg-red-500/10 text-red-400 border border-red-500/20'
                  }`}>
                    {preset.badge}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-1 italic">
                  "{preset.claim}"
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Submit Button with Loading State */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isLoading || !claimText.trim()}
            className={`w-full py-3.5 px-6 rounded-xl font-semibold text-sm flex items-center justify-center space-x-2 transition-all duration-200 shadow-lg ${
              isLoading || !claimText.trim()
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
                : 'bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold shadow-emerald-500/25 hover:shadow-emerald-500/40 border border-emerald-400/40 transform active:scale-[0.99]'
            }`}
          >
            {isLoading ? (
              <div className="flex items-center space-x-3 py-1">
                <svg className="animate-spin h-5 w-5 text-slate-950" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span className="font-mono text-xs sm:text-sm text-slate-950 font-bold">
                  {loadingMessages[loadingStep]}
                </span>
              </div>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-slate-950" />
                <span>Verify Claim with RAG Engine</span>
                <ArrowRight className="w-4 h-4 text-slate-950 ml-1" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
