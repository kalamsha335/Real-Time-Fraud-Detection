import React, { useState } from 'react';
import {
  Search,
  Filter,
  ArrowUpDown,
  ExternalLink,
  ShieldAlert,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  X
} from 'lucide-react';

export default function TransactionsView({ transactions }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [predictionFilter, setPredictionFilter] = useState('ALL');
  const [selectedTx, setSelectedTx] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  const handleCopy = (id) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filtered = (transactions || []).filter((tx) => {
    const matchesSearch =
      tx.transaction_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tx.amount.toString().includes(searchTerm);

    const matchesRisk = riskFilter === 'ALL' || tx.risk_level === riskFilter;

    const matchesPred =
      predictionFilter === 'ALL' ||
      (predictionFilter === 'FRAUD' && tx.prediction === 1) ||
      (predictionFilter === 'LEGIT' && tx.prediction === 0);

    return matchesSearch && matchesRisk && matchesPred;
  });

  return (
    <div className="space-y-5">
      {/* Search & Filter Toolbar */}
      <div className="p-4 rounded-2xl bg-navy-900 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4 shadow-sm">
        {/* Search Input */}
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Transaction ID or Amount..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-navy-950 border border-slate-700/80 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          <span className="text-xs text-slate-500 font-semibold mr-1 flex items-center space-x-1">
            <Filter className="w-3.5 h-3.5" />
            <span>Risk:</span>
          </span>
          {['ALL', 'LOW', 'MEDIUM', 'HIGH'].map((rf) => (
            <button
              key={rf}
              onClick={() => setRiskFilter(rf)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                riskFilter === rf
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
                  : 'bg-navy-950 text-slate-400 border border-slate-800 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              {rf}
            </button>
          ))}

          <span className="text-xs text-slate-500 font-semibold ml-3 mr-1">Class:</span>
          {['ALL', 'FRAUD', 'LEGIT'].map((pf) => (
            <button
              key={pf}
              onClick={() => setPredictionFilter(pf)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                predictionFilter === pf
                  ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40 shadow-sm'
                  : 'bg-navy-950 text-slate-400 border border-slate-800 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              {pf}
            </button>
          ))}
        </div>
      </div>

      {/* Transactions Table */}
      <div className="rounded-2xl bg-navy-900 border border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-navy-950/60 text-[11px] uppercase tracking-wider text-slate-400 font-bold">
                <th className="py-3.5 px-4">Transaction ID</th>
                <th className="py-3.5 px-4">Amount</th>
                <th className="py-3.5 px-4">Fraud Probability</th>
                <th className="py-3.5 px-4">Decision</th>
                <th className="py-3.5 px-4">Risk Tier</th>
                <th className="py-3.5 px-4">Timestamp</th>
                <th className="py-3.5 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-xs">
              {filtered.length > 0 ? (
                filtered.map((tx) => {
                  const isHigh = tx.risk_level === 'HIGH';
                  const isMed = tx.risk_level === 'MEDIUM';
                  const probPct = (tx.fraud_probability * 100).toFixed(1);

                  return (
                    <tr
                      key={tx.transaction_id}
                      className="hover:bg-slate-800/40 transition-colors"
                    >
                      {/* ID */}
                      <td className="py-3.5 px-4 font-mono text-slate-200">
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold text-slate-100">{tx.transaction_id.slice(0, 16)}...</span>
                          <button
                            onClick={() => handleCopy(tx.transaction_id)}
                            className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
                            title="Copy full UUID"
                          >
                            {copiedId === tx.transaction_id ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      </td>

                      {/* Amount */}
                      <td className="py-3.5 px-4 font-mono font-semibold text-white">
                        ${parseFloat(tx.amount).toFixed(2)}
                      </td>

                      {/* Probability with bar */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center space-x-2.5">
                          <span
                            className={`font-mono font-bold w-12 text-right ${
                              isHigh ? 'text-rose-400' : isMed ? 'text-amber-400' : 'text-emerald-400'
                            }`}
                          >
                            {probPct}%
                          </span>
                          <div className="w-20 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                isHigh ? 'bg-rose-500' : isMed ? 'bg-amber-500' : 'bg-emerald-500'
                              }`}
                              style={{ width: `${probPct}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Prediction */}
                      <td className="py-3.5 px-4">
                        {tx.prediction === 1 ? (
                          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
                            <ShieldAlert className="w-3 h-3" />
                            <span>FRAUD (1)</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>LEGITIMATE (0)</span>
                          </span>
                        )}
                      </td>

                      {/* Risk Level */}
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[11px] font-bold border ${
                            isHigh
                              ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                              : isMed
                              ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                              : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                          }`}
                        >
                          {tx.risk_level}
                        </span>
                      </td>

                      {/* Timestamp */}
                      <td className="py-3.5 px-4 text-slate-400 font-mono text-[11px]">
                        {new Date(tx.timestamp).toLocaleString()}
                      </td>

                      {/* Details Drawer Button */}
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => setSelectedTx(tx)}
                          className="px-3 py-1 rounded-lg bg-navy-950 border border-slate-700/80 hover:border-indigo-500 text-slate-300 hover:text-indigo-300 text-xs font-semibold transition-all"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500 font-medium">
                    No transactions match the selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Footer count */}
        <div className="p-4 border-t border-slate-800 bg-navy-950/50 text-xs text-slate-400 flex justify-between items-center font-medium">
          <span>
            Showing <strong className="text-white font-mono">{filtered.length}</strong> of{' '}
            <strong className="text-white font-mono">{transactions?.length || 0}</strong> transactions
          </span>
          <span className="text-[11px] text-slate-500">
            Validated against authentic 432-feature XGBoost schema
          </span>
        </div>
      </div>

      {/* Transaction Inspection Modal */}
      {selectedTx && (
        <div className="fixed inset-0 bg-navy-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-navy-900 border border-slate-700/80 rounded-2xl w-full max-w-xl p-6 shadow-2xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center space-x-2.5">
                <ShieldAlert className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-base text-white">Transaction Feature Inspector</h3>
              </div>
              <button
                onClick={() => setSelectedTx(null)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div className="p-3.5 rounded-xl bg-navy-950 border border-slate-800 font-mono text-xs space-y-2">
                <div className="flex justify-between text-slate-400">
                  <span>UUID:</span>
                  <span className="text-indigo-300 font-semibold select-all">{selectedTx.transaction_id}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Amount:</span>
                  <span className="text-white font-bold">${parseFloat(selectedTx.amount).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Fraud Probability:</span>
                  <span className="text-rose-400 font-bold">{(selectedTx.fraud_probability * 100).toFixed(2)}%</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Risk Stratification:</span>
                  <span className="text-amber-400 font-bold">{selectedTx.risk_level}</span>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                  Key Evaluated Features (432-Feature Schema)
                </h4>
                <div className="p-3 rounded-xl bg-navy-950 border border-slate-800 text-xs font-mono text-slate-300 space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-slate-400">ProductCD:</span>
                    <span className="text-indigo-300 font-semibold">"W"</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">card1 (Relationship Proxy):</span>
                    <span className="text-indigo-300 font-semibold">13926</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">card2:</span>
                    <span className="text-indigo-300 font-semibold">360.0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">card4:</span>
                    <span className="text-indigo-300 font-semibold">"visa"</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">card6:</span>
                    <span className="text-indigo-300 font-semibold">"debit"</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">addr1:</span>
                    <span className="text-indigo-300 font-semibold">315.0</span>
                  </div>
                  <div className="flex justify-between pt-1 border-t border-slate-800">
                    <span className="text-slate-400">Inference Pipeline:</span>
                    <span className="text-emerald-400 font-semibold">ColumnTransformer + XGBoost (0.50 Threshold)</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 text-right">
                <button
                  onClick={() => setSelectedTx(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-all"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
