import React from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  ShieldAlert,
  ArrowUpRight,
  Clock,
  Layers,
  Zap,
  Gauge,
  Sparkles
} from 'lucide-react';

export default function OverviewView({ metrics, transactions, alerts, setActiveTab, onOpenSimulate }) {
  const total = metrics?.total_transactions ?? 0;
  const fraud = metrics?.fraudulent_detected ?? metrics?.fraudulent_transactions ?? 0;
  const legit = metrics?.legitimate_transactions ?? (total >= fraud ? total - fraud : 0);
  const fraudRate = metrics?.fraud_detection_rate !== undefined
    ? Number(metrics.fraud_detection_rate).toFixed(2)
    : (total > 0 ? ((fraud / total) * 100).toFixed(2) : '0.00');
  const pendingAlerts = alerts?.filter(a => a.review_status === 'PENDING').length ?? 0;

  const lowRisk = metrics?.low_risk_count ?? metrics?.risk_distribution?.LOW ?? (total > 0 ? Math.max(0, legit - (metrics?.medium_risk_count ?? 0)) : 0);
  const medRisk = metrics?.medium_risk_count ?? metrics?.risk_distribution?.MEDIUM ?? 0;
  const highRisk = metrics?.high_risk_count ?? metrics?.risk_distribution?.HIGH ?? fraud;

  const lowPct = total > 0 ? ((lowRisk / total) * 100).toFixed(1) : '0.0';
  const medPct = total > 0 ? ((medRisk / total) * 100).toFixed(1) : '0.0';
  const highPct = total > 0 ? ((highRisk / total) * 100).toFixed(1) : '0.0';

  const statCards = [
    {
      title: 'Total Transactions',
      value: total.toLocaleString(),
      sub: 'Processed & Scored',
      icon: Activity,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10 border-indigo-500/20'
    },
    {
      title: 'Fraud Detected',
      value: fraud.toLocaleString(),
      sub: `${fraudRate}% detection rate`,
      icon: AlertTriangle,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/20'
    },
    {
      title: 'Legitimate Volume',
      value: legit.toLocaleString(),
      sub: `${(100 - parseFloat(fraudRate)).toFixed(2)}% cleared`,
      icon: CheckCircle,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20'
    },
    {
      title: 'Pending Triage Alerts',
      value: pendingAlerts.toString(),
      sub: 'Requires analyst review',
      icon: ShieldAlert,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20'
    }
  ];

  return (
    <div className="space-y-6">
      {/* 4 Primary Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`p-5 rounded-2xl bg-navy-900 border border-slate-800 shadow-md ${card.bg} hover:border-slate-700 transition-all`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  {card.title}
                </span>
                <div className="p-2.5 rounded-xl border">
                  <Icon className={`w-4 h-4 ${card.color}`} />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-bold text-white tracking-tight font-mono">
                  {card.value}
                </div>
                <p className="text-xs text-slate-400 mt-1 flex items-center space-x-1">
                  <span>{card.sub}</span>
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid: Risk Breakdown + Recent Suspicious Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Suspicious Activity */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-navy-900 border border-slate-800 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white">Recent Suspicious Transactions</h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                  Priority Queue
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">High and medium risk transactions flagged for analyst triage</p>
            </div>
            <button
              onClick={() => setActiveTab('alerts')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-navy-950 border border-indigo-500/20 hover:border-indigo-500/50 transition-all"
            >
              <span>View All Alerts</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="mt-4 divide-y divide-slate-800/80">
            {alerts && alerts.length > 0 ? (
              alerts.slice(0, 6).map((a) => (
                <div
                  key={a.alert_id}
                  className="py-3.5 flex items-center justify-between hover:bg-slate-800/40 px-3 rounded-xl transition-colors group cursor-pointer"
                  onClick={() => setActiveTab('alerts')}
                  title="Click to triage this alert"
                >
                  <div className="flex items-center space-x-3.5">
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
                      a.risk_level === 'HIGH'
                        ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                        : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                    }`}>
                      <ShieldAlert className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-semibold font-mono text-slate-100 group-hover:text-indigo-300 transition-colors">
                          {a.transaction_id}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          a.risk_level === 'HIGH'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        }`}>
                          {a.risk_level} RISK
                        </span>
                      </div>
                      <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1 font-medium">
                        <span className="font-semibold text-slate-200 font-mono">${parseFloat(a.amount).toFixed(2)}</span>
                        <span>•</span>
                        <span>Fraud Prob: <strong className={`font-mono ${a.risk_level === 'HIGH' ? 'text-rose-400' : 'text-amber-400'}`}>{(a.fraud_probability * 100).toFixed(1)}%</strong></span>
                        <span>•</span>
                        <span className="flex items-center space-x-1 text-slate-500">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className={`inline-block px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
                      a.review_status === 'PENDING'
                        ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                        : a.review_status === 'CONFIRMED_FRAUD'
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                        : a.review_status === 'INVESTIGATING'
                        ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40'
                        : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                    }`}>
                      {a.review_status.replace('_', ' ')}
                    </span>
                    <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                  </div>
                </div>
              ))
            ) : (
              <div className="py-14 text-center">
                <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-3">
                  <Zap className="w-6 h-6 text-indigo-400" />
                </div>
                <h4 className="text-sm font-semibold text-slate-200">No Suspicious Activity Flagged</h4>
                <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                  Click the <strong>Simulate Stream</strong> button in the header bar to inject live transaction events.
                </p>
                {onOpenSimulate && (
                  <button
                    onClick={onOpenSimulate}
                    className="mt-4 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-indigo-700 text-white text-xs font-semibold hover:from-blue-500 hover:to-indigo-600 transition-all shadow-md shadow-indigo-600/20"
                  >
                    Open Simulator Modal
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right 1 Col: Risk Stratification & Model Snapshot */}
        <div className="space-y-6">
          {/* Risk distribution */}
          <div className="p-6 rounded-2xl bg-navy-900 border border-slate-800 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white">Risk Stratification</h2>
              <Gauge className="w-4 h-4 text-indigo-400" />
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Distribution across evaluated transactions</p>

            <div className="mt-5 space-y-4">
              {/* Low Risk */}
              <div>
                <div className="flex justify-between text-xs mb-1.5 font-medium">
                  <span className="text-emerald-400">Low Risk (&lt; 0.30)</span>
                  <span className="text-slate-300 font-mono font-semibold">{lowRisk} ({lowPct}%)</span>
                </div>
                <div className="w-full h-2.5 bg-slate-800/80 rounded-full overflow-hidden p-0.5 border border-slate-800">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.max(0, parseFloat(lowPct)))}%` }}
                  />
                </div>
              </div>

              {/* Medium Risk */}
              <div>
                <div className="flex justify-between text-xs mb-1.5 font-medium">
                  <span className="text-amber-400">Medium Risk (0.30 - 0.50)</span>
                  <span className="text-slate-300 font-mono font-semibold">{medRisk} ({medPct}%)</span>
                </div>
                <div className="w-full h-2.5 bg-slate-800/80 rounded-full overflow-hidden p-0.5 border border-slate-800">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-orange-400 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.max(0, parseFloat(medPct)))}%` }}
                  />
                </div>
              </div>

              {/* High Risk */}
              <div>
                <div className="flex justify-between text-xs mb-1.5 font-medium">
                  <span className="text-rose-400">High Risk (≥ 0.50)</span>
                  <span className="text-slate-300 font-mono font-semibold">{highRisk} ({highPct}%)</span>
                </div>
                <div className="w-full h-2.5 bg-slate-800/80 rounded-full overflow-hidden p-0.5 border border-slate-800">
                  <div
                    className="h-full bg-gradient-to-r from-rose-500 to-red-600 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.max(0, parseFloat(highPct)))}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Model Snapshot Card */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-navy-900 via-navy-850 to-navy-900 border border-indigo-500/30 shadow-lg shadow-navy-950/40">
            <div className="flex items-center justify-between text-indigo-400 text-xs font-semibold uppercase tracking-wider">
              <div className="flex items-center space-x-2">
                <Layers className="w-4 h-4" />
                <span>Active Inference Pipeline</span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 font-mono font-semibold">
                XGBoost v1.0
              </span>
            </div>
            <div className="mt-3">
              <div className="text-sm font-bold text-white">Supervised Fraud Classification Model</div>
              <div className="text-xs text-slate-400 mt-1">
                Embedded ColumnTransformer + OneHotEncoder (432 input features)
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5 mt-4 pt-3 border-t border-slate-800 text-xs">
              <div className="p-2.5 rounded-xl bg-navy-950/80 border border-slate-800/80">
                <span className="text-slate-400 block text-[10px] font-medium">ROC-AUC</span>
                <span className="font-bold font-mono text-indigo-300 text-base">0.9086</span>
              </div>
              <div className="p-2.5 rounded-xl bg-navy-950/80 border border-slate-800/80">
                <span className="text-slate-400 block text-[10px] font-medium">PR-AUC</span>
                <span className="font-bold font-mono text-blue-400 text-base">0.5189</span>
              </div>
              <div className="p-2.5 rounded-xl bg-navy-950/80 border border-slate-800/80">
                <span className="text-slate-400 block text-[10px] font-medium">FRAUD RECALL</span>
                <span className="font-bold font-mono text-emerald-400 text-base">73.0%</span>
              </div>
              <div className="p-2.5 rounded-xl bg-navy-950/80 border border-slate-800/80">
                <span className="text-slate-400 block text-[10px] font-medium">PRECISION</span>
                <span className="font-bold font-mono text-amber-400 text-base">22.0%</span>
              </div>
            </div>
            <div className="mt-3 pt-2 text-[11px] text-slate-400 flex justify-between items-center font-mono">
              <span>Decision Threshold: <strong className="text-indigo-300">0.5000</strong></span>
              <span>Avg Latency: <strong className="text-emerald-300">{metrics?.average_latency_ms ? `${metrics.average_latency_ms.toFixed(1)}ms` : '~1.2ms'}</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
