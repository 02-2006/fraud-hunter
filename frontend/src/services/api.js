/**
 * FraudHunter AI — Frontend API Service
 * All HTTP calls to the FastAPI backend
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    let message = err.detail || `HTTP ${res.status}`
    if (Array.isArray(message)) {
      message = message.map(e => `${e.loc?.slice(-1)[0]}: ${e.msg}`).join(', ') // Format FastAPI validation errors
    } else if (typeof message === 'object') {
      message = JSON.stringify(message)
    }
    throw new Error(message)
  }
  return res.json()
}

export const api = {
  // ── Health ─────────────────────────────────────────────────────────────────
  health: () => request('/health'),

  // ── Transactions ───────────────────────────────────────────────────────────
  ingestTransaction: (tx) =>
    request('/api/v1/transactions/ingest', { method: 'POST', body: JSON.stringify(tx) }),

  ingestBatch: (txs) =>
    request('/api/v1/transactions/ingest/batch', { method: 'POST', body: JSON.stringify(txs) }),

  listTransactions: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/api/v1/transactions/?${qs}`)
  },

  getTransaction: (id) => request(`/api/v1/transactions/${id}`),

  decideTransaction: (id, action, reason) =>
    request(`/api/v1/transactions/${id}/decide`, {
      method: 'POST',
      body: JSON.stringify({ action, reason }),
    }),

  investigateTransaction: (transactionId, query = '') =>
    request('/api/v1/transactions/investigate', {
      method: 'POST',
      body: JSON.stringify({ transaction_id: transactionId, query }),
    }),

  // ── Agents ─────────────────────────────────────────────────────────────────
  listAgents: () => request('/api/v1/agents/'),

  commandAgent: (agentId, command, config = {}) =>
    request(`/api/v1/agents/${agentId}/command`, {
      method: 'POST',
      body: JSON.stringify({ command, config }),
    }),

  // ── Alerts ─────────────────────────────────────────────────────────────────
  getAlerts: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/api/v1/alerts/?${qs}`)
  },

  resolveAlert: (alertId) =>
    request(`/api/v1/alerts/${alertId}/resolve`, { method: 'POST' }),

  // ── Analytics ──────────────────────────────────────────────────────────────
  getDashboardStats: () => request('/api/v1/analytics/dashboard'),

  getRiskDistribution: () => request('/api/v1/analytics/risk-distribution'),

  getTimeSeries: (metric = 'fraud_count', hours = 24) =>
    request(`/api/v1/analytics/timeseries?metric=${metric}&hours=${hours}`),

  getTopPatterns: () => request('/api/v1/analytics/top-fraud-patterns'),

  // ── Cases ──────────────────────────────────────────────────────────────────
  listCases: () => request('/api/v1/cases/'),

  createCase: (payload) =>
    request('/api/v1/cases/', { method: 'POST', body: JSON.stringify(payload) }),

  getCase: (id) => request(`/api/v1/cases/${id}`),

  escalateCase: (id) =>
    request(`/api/v1/cases/${id}/escalate`, { method: 'POST' }),
}
