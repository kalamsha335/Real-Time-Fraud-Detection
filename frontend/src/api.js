/**
 * API client connecting the React Analyst Dashboard to the FastAPI backend.
 * Uses relative URL for dev proxy or explicit fallback to http://127.0.0.1:8000.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

async function fetchJSON(url, options = {}) {
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
  try {
    const res = await fetch(fullUrl, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options
    });

    if (!res.ok) {
      const errorText = await res.text();
      let errorJson = null;
      try {
        errorJson = JSON.parse(errorText);
      } catch (e) {
        // text format
      }
      throw new Error(errorJson?.detail || `HTTP Error ${res.status}: ${res.statusText}`);
    }

    return await res.json();
  } catch (err) {
    console.error(`API Call failed [${url}]:`, err);
    throw err;
  }
}

export const api = {
  // System & Health
  getHealth: () => fetchJSON('/health'),
  getRootStatus: () => fetchJSON('/'),
  getModelInfo: () => fetchJSON('/model/info'),

  // Metrics
  getMetrics: () => fetchJSON('/metrics'),

  // Transactions
  getTransactions: (params = {}) => {
    const query = new URLSearchParams();
    if (params.limit) query.append('limit', params.limit);
    if (params.risk_level) query.append('risk_level', params.risk_level);
    if (params.prediction !== undefined && params.prediction !== null) query.append('prediction', params.prediction);
    const qs = query.toString();
    return fetchJSON(`/transactions${qs ? `?${qs}` : ''}`);
  },

  getTransactionById: (id) => fetchJSON(`/transactions/${id}`),

  // Predict
  predictTransaction: (txPayload) => fetchJSON('/predict', {
    method: 'POST',
    body: JSON.stringify(txPayload)
  }),

  // Simulator
  injectSimulation: (scenario = 'random', count = 1) => fetchJSON('/simulator/inject', {
    method: 'POST',
    body: JSON.stringify({ scenario, count })
  }),

  // Alerts
  getAlerts: (params = {}) => {
    const query = new URLSearchParams();
    if (params.limit) query.append('limit', params.limit);
    if (params.review_status) query.append('review_status', params.review_status);
    if (params.risk_level) query.append('risk_level', params.risk_level);
    const qs = query.toString();
    return fetchJSON(`/alerts${qs ? `?${qs}` : ''}`);
  },

  updateAlertReview: (alertId, reviewStatus, notes = '') => fetchJSON(`/alerts/${alertId}/review`, {
    method: 'PATCH',
    body: JSON.stringify({
      review_status: reviewStatus,
      analyst_notes: notes,
      reviewed_by: 'security_analyst'
    })
  }),

  // Graph Analysis
  getGraphAnalysis: (limit = 100, fusionWeight = 0.15) => {
    const query = new URLSearchParams({
      limit: limit.toString(),
      fusion_weight: fusionWeight.toString()
    });
    return fetchJSON(`/graph/analysis?${query.toString()}`);
  },

  // Monitoring & Drift
  getDriftMetrics: () => fetchJSON('/monitoring/drift'),
  getMlflowRuns: () => fetchJSON('/monitoring/mlflow/runs'),
  getModelSummary: () => fetchJSON('/monitoring/model-summary'),
  triggerDriftRun: () => fetchJSON('/monitoring/drift/run', { method: 'POST' }),

  // Full HTML report link
  getDriftReportUrl: () => `${API_BASE_URL}/monitoring/drift/report`
};
