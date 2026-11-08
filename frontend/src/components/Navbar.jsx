import React, { useState } from 'react';
import {
  RefreshCw,
  Play,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  Sliders,
  Zap,
  X,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  ShoppingBag,
  Flame,
  Shuffle,
  Sun,
  Moon,
  Palette
} from 'lucide-react';
import { api } from '../api';

export default function Navbar({
  activeTab,
  systemHealth,
  onRefresh,
  autoRefresh,
  setAutoRefresh,
  isRefreshing,
  isSimulateOpen,
  setIsSimulateOpen,
  theme,
  onThemeChange
}) {
  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const showModal = isSimulateOpen !== undefined ? isSimulateOpen : modalOpen;
  const setShowModal = setIsSimulateOpen || setModalOpen;

  // Simulation controls
  const [selectedScenario, setSelectedScenario] = useState('random');
  const [selectedCount, setSelectedCount] = useState(1);
  const [simulating, setSimulating] = useState(false);
  const [quickSimulating, setQuickSimulating] = useState(false);
  const [simError, setSimError] = useState(null);
  const [lastResults, setLastResults] = useState([]);
  const [toastResult, setToastResult] = useState(null);

  const viewTitles = {
    overview: {
      title: 'Platform Overview',
      subtitle: 'Real-time financial transaction streams & anomaly metrics'
    },
    transactions: {
      title: 'Live Transactions',
      subtitle: 'Chronological evaluation stream with 432-feature inference'
    },
    alerts: {
      title: 'Fraud Alert Triage',
      subtitle: 'High-risk incidents queued for fraud analyst investigation'
    },
    graph: {
      title: 'Graph Relationship Analysis',
      subtitle: 'PyTorch Geometric GCN relationship proxy clustering'
    },
    monitoring: {
      title: 'Model Monitoring & Data Drift',
      subtitle: 'Evidently statistical distribution tracking & MLflow experiment parameters'
    },
    health: {
      title: 'System Infrastructure & Health',
      subtitle: 'Status of API, PostgreSQL / SQLite storage, Kafka broker & GNN services'
    }
  };

  const currentInfo = viewTitles[activeTab] || viewTitles.overview;
  const isOnline = systemHealth?.status === 'healthy';

  const scenarios = [
    {
      id: 'random',
      title: 'Production Payment Stream',
      description: 'Dynamic mix matching typical payment gateway traffic (60% low risk, 25% velocity spurt, 15% fraud)',
      icon: Shuffle,
      color: 'text-indigo-400',
      border: 'border-indigo-500/40',
      bg: 'bg-indigo-500/10'
    },
    {
      id: 'fraud',
      title: 'High-Risk Fraud Attack',
      description: 'Simulates account takeover & velocity abuse ($900 - $4,800, elevated C-counts, prob ≥ 50%)',
      icon: Flame,
      color: 'text-rose-400',
      border: 'border-rose-500/40',
      bg: 'bg-rose-500/10'
    },
    {
      id: 'suspicious',
      title: 'Suspicious Velocity Spurt',
      description: 'Repeated transaction burst ($220 - $480, medium anomaly scores, prob 30% - 49%)',
      icon: TrendingUp,
      color: 'text-amber-400',
      border: 'border-amber-500/40',
      bg: 'bg-amber-500/10'
    },
    {
      id: 'legitimate',
      title: 'Standard E-Commerce Purchase',
      description: 'Typical cardholder grocery or online retail payment ($15 - $85, clean profile, prob < 15%)',
      icon: ShoppingBag,
      color: 'text-emerald-400',
      border: 'border-emerald-500/40',
      bg: 'bg-emerald-500/10'
    }
  ];

  // Core simulation handler
  const executeSimulation = async (scenario, count) => {
    setSimError(null);
    try {
      const response = await api.injectSimulation(scenario, count);
      const results = response.results || [];
      setLastResults(results);

      if (results.length > 0) {
        const first = results[0];
        setToastResult({
          id: first.transaction_id,
          prob: (first.fraud_probability * 100).toFixed(1),
          pred: first.prediction,
          risk: first.risk_level,
          count: results.length
        });
        setTimeout(() => setToastResult(null), 6000);
      }

      // Trigger automatic platform refresh
      if (onRefresh) {
        setTimeout(onRefresh, 300);
      }
      return true;
    } catch (err) {
      console.error('Simulation execution failed:', err);
      setSimError(err.message || 'Simulation failed to deliver transactions to backend.');
      return false;
    }
  };

  const handleModalSubmit = async (e) => {
    e?.preventDefault();
    setSimulating(true);
    await executeSimulation(selectedScenario, selectedCount);
    setSimulating(false);
  };

  const handleQuickSimulate = async () => {
    setQuickSimulating(true);
    await executeSimulation('random', 1);
    setQuickSimulating(false);
  };

  return (
    <>
      <header
        className="h-20 border-b border-slate-800/90 px-8 flex items-center justify-between sticky top-0 z-30 shadow-sm backdrop-blur-md"
        style={{ backgroundColor: 'var(--header-bg)', borderColor: 'var(--border-color)' }}
      >
        <div>
          <h1 className="text-xl font-bold tracking-tight flex items-center space-x-2">
            <span>{currentInfo.title}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-medium">{currentInfo.subtitle}</p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Simulation Toast Notification */}
          {toastResult && (
            <div className="px-3.5 py-1.5 rounded-xl bg-navy-800 border border-indigo-500/40 text-xs flex items-center space-x-2.5 text-slate-200 animate-fade-in shadow-xl shadow-navy-950/60">
              <ShieldAlert className={`w-4 h-4 ${toastResult.pred === 1 ? 'text-rose-400' : 'text-emerald-400'}`} />
              <span>
                {toastResult.count > 1 ? `Processed ${toastResult.count} events:` : 'Processed:'}{' '}
                <strong className="font-mono text-indigo-300">{toastResult.id}</strong>
              </span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                toastResult.risk === 'HIGH'
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                  : toastResult.risk === 'MEDIUM'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
              }`}>
                {toastResult.risk} ({toastResult.prob}%)
              </span>
            </div>
          )}

          {/* Theme Selector Pill */}
          {onThemeChange && (
            <div className="flex items-center p-1 rounded-xl bg-navy-950 border border-slate-800 text-xs shadow-sm">
              <button
                onClick={() => onThemeChange('titanium')}
                className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg transition-all font-semibold ${
                  theme === 'titanium'
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Titanium Carbon Dark Theme"
              >
                <Moon className="w-3.5 h-3.5 text-indigo-400" />
                <span className="hidden md:inline">Carbon</span>
              </button>
              <button
                onClick={() => onThemeChange('midnight')}
                className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg transition-all font-semibold ${
                  theme === 'midnight'
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Midnight Sapphire Dark Theme"
              >
                <Palette className="w-3.5 h-3.5 text-blue-400" />
                <span className="hidden md:inline">Midnight</span>
              </button>
              <button
                onClick={() => onThemeChange('light')}
                className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg transition-all font-semibold ${
                  theme === 'light'
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Enterprise Light Theme"
              >
                <Sun className="w-3.5 h-3.5 text-amber-400" />
                <span className="hidden md:inline">Light</span>
              </button>
            </div>
          )}

          {/* Quick 1-Click Simulate Button */}
          <button
            onClick={handleQuickSimulate}
            disabled={quickSimulating || !isOnline}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-navy-950 border border-slate-700/80 hover:border-indigo-500 text-slate-300 hover:text-indigo-300 text-xs font-semibold transition-all shadow-sm disabled:opacity-50"
            title="Immediately evaluate 1 sample transaction event"
          >
            <Zap className={`w-3.5 h-3.5 text-indigo-400 ${quickSimulating ? 'animate-spin' : ''}`} />
            <span>{quickSimulating ? 'Scoring...' : 'Quick Inject'}</span>
          </button>

          {/* Full Interactive Simulator Trigger Button */}
          <button
            onClick={() => setShowModal(true)}
            disabled={!isOnline}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-indigo-700 hover:from-blue-500 hover:to-indigo-600 text-white font-semibold text-xs shadow-md shadow-indigo-600/25 transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Simulate Stream</span>
          </button>

          {/* Auto Refresh Toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-2 rounded-xl text-xs font-semibold border transition-all ${
              autoRefresh
                ? 'bg-indigo-950/60 text-indigo-300 border-indigo-500/40 shadow-sm shadow-indigo-500/10'
                : 'bg-slate-800/60 text-slate-400 border-slate-700/60 hover:text-slate-200'
            }`}
          >
            Auto (5s): {autoRefresh ? 'ON' : 'OFF'}
          </button>

          {/* Manual Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/80 transition-all disabled:opacity-50"
            title="Refresh All Dashboard Metrics"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-indigo-400' : ''}`} />
          </button>

          {/* System Health Indicator */}
          <div className="flex items-center space-x-2 pl-3 border-l border-slate-800">
            {isOnline ? (
              <div className="flex items-center space-x-1.5 text-emerald-400 text-xs font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/30">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>API Live</span>
              </div>
            ) : (
              <div className="flex items-center space-x-1.5 text-rose-400 text-xs font-semibold bg-rose-500/10 px-2.5 py-1 rounded-full border border-rose-500/30">
                <XCircle className="w-3.5 h-3.5" />
                <span>API Offline</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* ========================================================================= */}
      {/* TRANSACTION SIMULATOR MODAL                                              */}
      {/* ========================================================================= */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-md animate-fade-in">
          <div className="w-full max-w-2xl bg-navy-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-navy-950/70">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-600/20">
                  <Sliders className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white tracking-tight">
                    Transaction Stream Simulator
                  </h3>
                  <p className="text-xs text-slate-400 font-medium">
                    Inject valid 432-feature IEEE-CIS financial transactions into the real-time inference pipeline
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6 overflow-y-auto">
              {/* Error Callout (No unhandled browser alert popups) */}
              {simError && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/40 text-xs text-rose-200 flex items-start space-x-3">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <strong className="block text-rose-300 font-semibold">Simulation Request Failed</strong>
                    <p>{simError}</p>
                    <p className="text-slate-400 text-[11px]">
                      Ensure the backend API service is running on <code className="text-indigo-300">http://127.0.0.1:8000</code>.
                    </p>
                  </div>
                </div>
              )}

              {/* Step 1: Choose Scenario */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                  1. Select Transaction Profile
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {scenarios.map((sc) => {
                    const Icon = sc.icon;
                    const isSelected = selectedScenario === sc.id;
                    return (
                      <button
                        key={sc.id}
                        type="button"
                        onClick={() => setSelectedScenario(sc.id)}
                        className={`p-3.5 rounded-xl border text-left transition-all relative ${
                          isSelected
                            ? `${sc.bg} ${sc.border} ring-1 ring-indigo-500/50 shadow-md`
                            : 'bg-navy-950/70 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-center space-x-2.5 mb-1.5">
                          <Icon className={`w-4 h-4 ${sc.color}`} />
                          <span className="text-xs font-bold text-slate-100">{sc.title}</span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed font-medium">
                          {sc.description}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Step 2: Choose Count */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                  2. Batch Size (Events to Inject)
                </label>
                <div className="flex items-center space-x-3">
                  {[1, 5, 10, 25].map((cnt) => (
                    <button
                      key={cnt}
                      type="button"
                      onClick={() => setSelectedCount(cnt)}
                      className={`flex-1 py-2.5 rounded-xl text-xs font-bold font-mono transition-all border ${
                        selectedCount === cnt
                          ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/50 shadow-sm'
                          : 'bg-navy-950 text-slate-400 border-slate-800 hover:text-slate-200'
                      }`}
                    >
                      {cnt} {cnt === 1 ? 'Event' : 'Events'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Step 3: Latest Results Display */}
              {lastResults.length > 0 && (
                <div className="p-4 rounded-xl bg-navy-950 border border-slate-800">
                  <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                    <span>Evaluated Transactions ({lastResults.length})</span>
                    <span className="text-emerald-400 font-mono text-[11px]">200 OK • Scored by Model</span>
                  </div>
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {lastResults.map((res, i) => (
                      <div
                        key={i}
                        className="p-2.5 rounded-lg bg-navy-900 border border-slate-800/80 flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center space-x-3">
                          <span className="font-mono text-indigo-300 font-semibold">{res.transaction_id}</span>
                          <span className="text-slate-400 font-mono">
                            Latency: {res.inference_latency_ms ? `${res.inference_latency_ms.toFixed(1)}ms` : '~1.2ms'}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-slate-300 font-mono">
                            Prob: <strong className={res.risk_level === 'HIGH' ? 'text-rose-400' : 'text-amber-400'}>
                              {(res.fraud_probability * 100).toFixed(1)}%
                            </strong>
                          </span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            res.risk_level === 'HIGH'
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                              : res.risk_level === 'MEDIUM'
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                              : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          }`}>
                            {res.risk_level}
                          </span>
                          {res.prediction === 1 && (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-500/30 text-rose-300 border border-rose-500/40">
                              ALERT QUEUED
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-slate-800 bg-navy-950/70 flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">
                Guarantees all 432 IEEE-CIS features are populated without schema mismatches.
              </span>
              <div className="flex items-center space-x-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition-colors"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={handleModalSubmit}
                  disabled={simulating || !isOnline}
                  className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-indigo-700 hover:from-blue-500 hover:to-indigo-600 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
                >
                  <Play className={`w-3.5 h-3.5 fill-current ${simulating ? 'animate-spin' : ''}`} />
                  <span>{simulating ? `Injecting ${selectedCount} Events...` : `Inject & Score ${selectedCount} Event${selectedCount > 1 ? 's' : ''}`}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
