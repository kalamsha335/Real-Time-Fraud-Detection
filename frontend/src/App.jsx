import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import OverviewView from './components/OverviewView';
import TransactionsView from './components/TransactionsView';
import AlertsView from './components/AlertsView';
import GraphView from './components/GraphView';
import MonitoringView from './components/MonitoringView';
import HealthView from './components/HealthView';
import { api } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSimulateOpen, setIsSimulateOpen] = useState(false);
  
  // Theme state: default to 'titanium' (modern carbon dark), supports 'midnight' and 'light'
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('fraud_sentinel_theme') || 'titanium';
  });

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
    localStorage.setItem('fraud_sentinel_theme', newTheme);
  };

  // Core platform states
  const [systemHealth, setSystemHealth] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setIsRefreshing(true);
      const [healthRes, metricsRes, txRes, alertsRes] = await Promise.allSettled([
        api.getHealth(),
        api.getMetrics(),
        api.getTransactions({ limit: 100 }),
        api.getAlerts({ limit: 50 })
      ]);

      if (healthRes.status === 'fulfilled') {
        setSystemHealth(healthRes.value);
        setError(null);
      } else {
        setSystemHealth({ status: 'unreachable', model_loaded: false });
      }

      if (metricsRes.status === 'fulfilled') {
        setMetrics(metricsRes.value);
      }

      if (txRes.status === 'fulfilled') {
        setTransactions(txRes.value.transactions || []);
      }

      if (alertsRes.status === 'fulfilled') {
        setAlerts(alertsRes.value.alerts || []);
      }
    } catch (err) {
      console.error('Failed to refresh dashboard data:', err);
      setError(err.message);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Periodic polling if autoRefresh is enabled
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchData();
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  const alertCount = alerts.filter(a => a.review_status === 'PENDING').length;

  return (
    <div
      className={`theme-${theme} min-h-screen font-sans transition-colors duration-300 selection:bg-indigo-500/30 selection:text-indigo-200`}
      style={{ backgroundColor: 'var(--bg-app)', color: 'var(--text-main)' }}
    >
      <div className="flex min-h-screen ambient-bg">
        {/* Sidebar Navigation */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          systemHealth={systemHealth}
          alertCount={alertCount}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <Navbar
            activeTab={activeTab}
            systemHealth={systemHealth}
            onRefresh={fetchData}
            autoRefresh={autoRefresh}
            setAutoRefresh={setAutoRefresh}
            isRefreshing={isRefreshing}
            isSimulateOpen={isSimulateOpen}
            setIsSimulateOpen={setIsSimulateOpen}
            theme={theme}
            onThemeChange={handleThemeChange}
          />

          <main className="flex-1 p-8 overflow-y-auto">
            {error && (
              <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 flex items-center justify-between shadow-lg">
                <span>Could not reach backend API at <strong className="font-mono text-white">http://127.0.0.1:8000</strong>. Make sure Uvicorn is active.</span>
                <button
                  onClick={fetchData}
                  className="px-3 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 font-bold border border-rose-500/40 transition-colors"
                >
                  Retry
                </button>
              </div>
            )}

            {activeTab === 'overview' && (
              <OverviewView
                metrics={metrics}
                transactions={transactions}
                alerts={alerts}
                setActiveTab={setActiveTab}
                onOpenSimulate={() => setIsSimulateOpen(true)}
              />
            )}

            {activeTab === 'transactions' && (
              <TransactionsView
                transactions={transactions}
              />
            )}

            {activeTab === 'alerts' && (
              <AlertsView
                alerts={alerts}
                onAlertUpdated={fetchData}
              />
            )}

            {activeTab === 'graph' && (
              <GraphView />
            )}

            {activeTab === 'monitoring' && (
              <MonitoringView />
            )}

            {activeTab === 'health' && (
              <HealthView
                systemHealth={systemHealth}
                onRefresh={fetchData}
              />
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
