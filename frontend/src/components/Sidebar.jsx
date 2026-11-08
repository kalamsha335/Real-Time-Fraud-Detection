import React from 'react';
import {
  LayoutDashboard,
  Activity,
  AlertTriangle,
  Share2,
  LineChart,
  Server,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, systemHealth, alertCount }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'transactions', label: 'Live Transactions', icon: Activity },
    { id: 'alerts', label: 'Fraud Alerts', icon: AlertTriangle, badge: alertCount },
    { id: 'graph', label: 'Graph Analysis', icon: Share2 },
    { id: 'monitoring', label: 'Model Monitoring', icon: LineChart },
    { id: 'health', label: 'System Health', icon: Server, statusDot: systemHealth?.status === 'healthy' }
  ];

  return (
    <aside className="w-64 bg-navy-900 border-r border-slate-800/90 flex flex-col justify-between shrink-0 h-screen sticky top-0 shadow-lg select-none">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800/90 flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 flex items-center justify-center shadow-md shadow-indigo-600/20">
            <ShieldCheck className="w-5 h-5 text-white stroke-[2.2]" />
          </div>
          <div>
            <div className="font-bold text-base tracking-tight text-white flex items-center space-x-1.5">
              <span>FraudSentinel</span>
              <span className="text-[9px] font-bold tracking-wider px-1.5 py-0.5 rounded bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Real-Time Risk Platform</p>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="p-3.5 space-y-1">
          <div className="px-3 py-2 text-[10px] font-bold tracking-wider text-slate-500 uppercase">
            Operations & Analytics
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/35 shadow-sm shadow-indigo-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  {item.badge > 0 && (
                    <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/40">
                      {item.badge}
                    </span>
                  )}
                  {item.statusDot !== undefined && (
                    <span
                      className={`w-2 h-2 rounded-full ${
                        item.statusDot ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50' : 'bg-rose-500'
                      }`}
                    />
                  )}
                  {isActive && <ChevronRight className="w-3.5 h-3.5 text-indigo-400" />}
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status */}
      <div className="p-4 m-3.5 rounded-xl bg-navy-950/80 border border-slate-800/80 text-xs">
        <div className="flex items-center justify-between text-slate-400 mb-1.5">
          <span className="text-[10px] uppercase tracking-wider font-bold text-slate-500">Pipeline Engine</span>
          <span className="inline-flex items-center space-x-1.5 text-emerald-400 font-mono text-[10px]">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>XGBoost v1.0</span>
          </span>
        </div>
        <div className="text-[11px] text-slate-400 font-mono flex justify-between pt-1.5 border-t border-slate-800/90">
          <span>Features: <strong className="text-slate-200">432</strong></span>
          <span>Thresh: <strong className="text-indigo-300">0.50</strong></span>
        </div>
      </div>
    </aside>
  );
}
