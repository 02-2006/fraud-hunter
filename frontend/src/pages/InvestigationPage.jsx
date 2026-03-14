// InvestigationPage.jsx
import { useState } from 'react'
import { api } from '../services/api'

export default function InvestigationPage() {
  const [txId, setTxId] = useState('')
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function runInvestigation() {
    if (!txId.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.investigateTransaction(txId.trim(), query)
      setResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const RISK_COLOR = { critical: '#ff3d5a', high: '#ffb020', medium: '#6699ff', low: '#6b7280', clear: '#00e5a0' }

  return (
    <div style={{ padding: 24, maxWidth: 800, color: '#e8eaf0' }}>
      <h2 style={{ fontSize: 20, fontWeight: 800, marginBottom: 24 }}>AI Deep Investigation</h2>

      <div style={{ background: '#0f1217', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: 20, marginBottom: 20 }}>
        <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>Transaction ID</div>
        <input
          value={txId}
          onChange={e => setTxId(e.target.value)}
          placeholder="e.g. TXN-9921 or UUID"
          style={{ width: '100%', background: '#141820', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '10px 14px', color: '#e8eaf0', fontSize: 13, fontFamily: 'monospace', outline: 'none', marginBottom: 12 }}
        />
        <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>Investigation Query (optional)</div>
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Focus investigation on velocity patterns, geo anomalies, or ring detection..."
          rows={3}
          style={{ width: '100%', background: '#141820', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '10px 14px', color: '#e8eaf0', fontSize: 13, fontFamily: 'inherit', outline: 'none', resize: 'vertical', marginBottom: 14 }}
        />
        <button onClick={runInvestigation} disabled={loading} style={{ background: '#00e5a0', border: 'none', borderRadius: 8, padding: '10px 24px', color: '#000', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>
          {loading ? 'Investigating...' : '⚡ Run AI Investigation'}
        </button>
        {error && <div style={{ marginTop: 10, color: '#ff3d5a', fontSize: 12 }}>{error}</div>}
      </div>

      {result && (
        <div style={{ background: '#0f1217', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, fontFamily: 'monospace' }}>Investigation Complete</div>
              <div style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>{result.investigation_time_ms}ms · {result.recommended_action}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 24, fontWeight: 800, fontFamily: 'monospace', color: RISK_COLOR[result.risk_verdict] }}>
                {Math.round(result.confidence * 100)}%
              </div>
              <div style={{ fontSize: 10, color: RISK_COLOR[result.risk_verdict], textTransform: 'uppercase', fontFamily: 'monospace' }}>{result.risk_verdict}</div>
            </div>
          </div>

          {result.key_findings.length > 0 && (
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1, fontFamily: 'monospace' }}>Key Findings</div>
              {result.key_findings.map((f, i) => (
                <div key={i} style={{ borderLeft: `2px solid ${RISK_COLOR[result.risk_verdict]}`, paddingLeft: 10, marginBottom: 6, fontSize: 12, color: RISK_COLOR[result.risk_verdict], fontFamily: 'monospace' }}>{f}</div>
              ))}
            </div>
          )}

          <div style={{ background: '#141820', borderRadius: 8, padding: 14, fontSize: 12, lineHeight: 1.7, color: '#e8eaf0', whiteSpace: 'pre-wrap' }}>
            <div style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 1.5, color: '#00e5a0', fontFamily: 'monospace', marginBottom: 8 }}>● AI Reasoning</div>
            {result.reasoning}
          </div>
        </div>
      )}
    </div>
  )
}
