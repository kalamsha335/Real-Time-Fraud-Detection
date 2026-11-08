import React, { useState } from 'react';
import {
  ShieldAlert,
  Clock,
  CheckCircle,
  XCircle,
  AlertOctagon,
  FileText,
  UserCheck,
  Search,
  MessageSquare,
  Send
} from 'lucide-react';
import { api } from '../api';

export default function AlertsView({ alerts, onAlertUpdated }) {
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [actionNotes, setActionNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [updateError, setUpdateError] = useState(null);

  const reviewStatuses = [
    { id: 'PENDING', label: 'Pending', color: 'bg-amber-500/20 text-amber-300 border-amber-500/40' },
    { id: 'INVESTIGATING', label: 'Investigating', color: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40' },
    { id: 'CONFIRMED_FRAUD', label: 'Confirmed Fraud', color: 'bg-rose-500/20 text-rose-300 border-rose-500/40' },
    { id: 'FALSE_POSITIVE', label: 'False Positive', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' }
  ];

  const handleUpdateStatus = async (alertId, newStatus) => {
    try {
      setSubmitting(true);
      setUpdateError(null);
      await api.updateAlertReview(alertId, newStatus, actionNotes || `Status updated to ${newStatus}`);
      setActionNotes('');
      if (selectedAlert && selectedAlert.alert_id === alertId) {
        setSelectedAlert(prev => ({ ...prev, review_status: newStatus }));
      }
      onAlertUpdated();
    } catch (err) {
      console.error('Failed to update alert:', err);
      setUpdateError(err.message || 'Failed to update alert review status.');
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = (alerts || []).filter((a) => {
    const matchesSearch =
      a.transaction_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.alert_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.amount.toString().includes(searchTerm);

    const matchesStatus = statusFilter === 'ALL' || a.review_status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Search and Status Pills */}
      <div className="p-4 rounded-2xl bg-navy-900 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4 shadow-sm">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search Alert or Transaction UUID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-navy-950 border border-slate-700/80 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        <div className="flex items-center space-x-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          <span className="text-xs text-slate-500 font-semibold mr-1">Status:</span>
          {['ALL', 'PENDING', 'INVESTIGATING', 'CONFIRMED_FRAUD', 'FALSE_POSITIVE'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                statusFilter === st
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
                  : 'bg-navy-950 text-slate-400 border border-slate-800 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts Grid & Triage Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Alerts List */}
        <div className="lg:col-span-2 space-y-3">
          {filtered.length > 0 ? (
            filtered.map((alt) => {
              const isSelected = selectedAlert?.alert_id === alt.alert_id;
              const probPct = (alt.fraud_probability * 100).toFixed(1);

              return (
                <div
                  key={alt.alert_id}
                  onClick={() => setSelectedAlert(alt)}
                  className={`p-5 rounded-2xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-navy-850 border-indigo-500/60 shadow-lg shadow-indigo-500/10'
                      : 'bg-navy-900 border border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3.5">
                      <div className="w-9 h-9 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center shrink-0 mt-0.5">
                        <AlertOctagon className="w-5 h-5 text-rose-400" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-sm font-bold text-white">
                            {alt.transaction_id}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            alt.risk_level === 'HIGH'
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                              : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                          }`}>
                            {alt.risk_level} RISK
                          </span>
                        </div>
                        <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1 font-medium">
                          <span className="font-mono font-semibold text-white">
                            ${parseFloat(alt.amount).toFixed(2)}
                          </span>
                          <span>•</span>
                          <span>Fraud Probability: <strong className="text-rose-400 font-mono">{probPct}%</strong></span>
                          <span>•</span>
                          <span className="flex items-center space-x-1 text-slate-500">
                            <Clock className="w-3 h-3" />
                            <span>{new Date(alt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                          </span>
                        </div>
                      </div>
                    </div>

                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                        alt.review_status === 'PENDING'
                          ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                          : alt.review_status === 'CONFIRMED_FRAUD'
                          ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                          : alt.review_status === 'INVESTIGATING'
                          ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40'
                          : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                      }`}
                    >
                      {alt.review_status.replace('_', ' ')}
                    </span>
                  </div>

                  {alt.suspicious_factors && alt.suspicious_factors.length > 0 && (
                    <div className="mt-3.5 pt-3 border-t border-slate-800/80 flex flex-wrap gap-1.5">
                      {alt.suspicious_factors.map((f, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded-md bg-navy-950 border border-slate-800 text-[11px] text-slate-300 font-mono"
                        >
                          {f}
                        </span>
                      ))}
                    </div>
                  )}

                  {alt.analyst_notes && (
                    <div className="mt-2.5 text-xs text-slate-400 italic bg-navy-950/60 p-2.5 rounded-xl border border-slate-800">
                      Notes: {alt.analyst_notes}
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="p-12 text-center rounded-2xl bg-navy-900 border border-slate-800 text-slate-500 text-xs font-medium">
              No alerts match the selected status filter.
            </div>
          )}
        </div>

        {/* Right 1 Col: Analyst Triage Actions */}
        <div className="space-y-5">
          <div className="p-6 rounded-2xl bg-navy-900 border border-slate-800 shadow-sm sticky top-24">
            <div className="flex items-center space-x-2 pb-4 border-b border-slate-800 text-white font-bold text-sm">
              <UserCheck className="w-4 h-4 text-indigo-400" />
              <span>Analyst Triage Action</span>
            </div>

            {updateError && (
              <div className="mt-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
                {updateError}
              </div>
            )}

            {selectedAlert ? (
              <div className="mt-4 space-y-4">
                <div className="p-3.5 rounded-xl bg-navy-950 border border-slate-800 font-mono text-xs space-y-2">
                  <div className="text-slate-400">Selected Alert:</div>
                  <div className="text-indigo-300 font-semibold break-all">{selectedAlert.alert_id}</div>
                  <div className="text-slate-400 mt-2">Transaction ID:</div>
                  <div className="text-slate-200 break-all">{selectedAlert.transaction_id}</div>
                  <div className="flex justify-between pt-2 border-t border-slate-800/80 text-slate-400">
                    <span>Amount:</span>
                    <span className="text-white font-bold">${parseFloat(selectedAlert.amount).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Fraud Prob:</span>
                    <span className="text-rose-400 font-bold">{(selectedAlert.fraud_probability * 100).toFixed(1)}%</span>
                  </div>
                </div>

                {/* Status Update Buttons */}
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
                    Update Investigation Status:
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {reviewStatuses.map((st) => (
                      <button
                        key={st.id}
                        onClick={() => handleUpdateStatus(selectedAlert.alert_id, st.id)}
                        disabled={submitting || selectedAlert.review_status === st.id}
                        className={`px-3 py-2 rounded-xl text-xs font-bold border transition-all text-center disabled:opacity-40 ${
                          selectedAlert.review_status === st.id
                            ? `${st.color} shadow-sm`
                            : 'bg-navy-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                        }`}
                      >
                        {st.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Add notes */}
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1.5">
                    Analyst Investigation Log / Notes:
                  </label>
                  <div className="relative">
                    <textarea
                      rows={3}
                      placeholder="Add investigation remarks (e.g., customer called, cardholder dispute, verified proxy)..."
                      value={actionNotes}
                      onChange={(e) => setActionNotes(e.target.value)}
                      className="w-full p-3 bg-navy-950 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none transition-colors"
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-slate-500 text-xs font-medium">
                Select an alert from the queue to review details and record analyst decisions.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
