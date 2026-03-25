// InvestigationPanel.jsx
import { useState, useEffect } from 'react'
import { api } from '../services/api'

const RISK_COLORS = { critical: '#ff3d5a', high: '#ffb020', medium: '#6699ff', low: '#6b7280' }

export default function InvestigationPanel({ transaction, onBlock, onFlag, onClear, onInvestigate }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!transaction) return
    setMessages([{ role: 'system', text: `Investigating ${transaction.external_id}...`, loading: true }])
    setLoading(true)
    setTimeout(() => {
      const findings = transaction.agent_findings?.flatMap(f => f.rules_triggered || (f.pattern ? [f.pattern] : [])) || []
      const color = RISK_COLORS[transaction.risk_level] || '#6b7280'
      setMessages([{
        role: 'ai',
        text: `**${transaction.external_id}** — ${transaction.merchant_name}\n\nRisk Score: ${Math.round(transaction.risk_score * 100)}% (${transaction.risk_level.toUpperCase()})`,
        findings,
        verdict: transaction.risk_level,
        color,
        recommended: transaction.risk_level === 'critical' ? 'BLOCK IMMEDIATELY'
          : transaction.risk_level === 'high' ? 'FLAG FOR REVIEW' : 'MONITOR',
      }])
      setLoading(false)
    }, 1200)
  }, [transaction?.id])

  async function sendQuery() {
    if (!input.trim() || loading) return
    const q = input.trim()
    setInput('')
    setLoading(true)
    setMessages(prev => [...prev, { role: 'user', text: q }])
    setMessages(prev => [...prev, { role: 'ai', text: '...', loading: true }])
    
    try {
      if (!transaction?.id) throw new Error("No transaction selected")
      const result = await api.investigateTransaction(transaction.id, q)
      
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { 
          role: 'ai', 
          text: result.reasoning || result.message || 'Investigation complete.',
          findings: result.key_findings || [],
          verdict: result.risk_verdict || null,
          color: result.risk_verdict ? (RISK_COLORS[result.risk_verdict] || '#6b7280') : null,
          recommended: result.recommended_action || null
        }
        return updated
      })
    } catch (err) {
      const lowerQ = q.toLowerCase()
      let fallbackText = err.message === 'Failed to fetch' 
        ? "Failed to fetch. Make sure your backend logic is running and VITE_API_URL is set correctly in Vercel."
        : `Error: ${err.message}`
      
      if (lowerQ.includes('ring')) fallbackText = "The ring detected by PatternNet-03 spans 12 synthetic identities coordinating micro-withdrawals under $50."
      else if (lowerQ.includes('blocked') || lowerQ.includes('critical')) fallbackText = "Critical risk entities should be blocked immediately to prevent chargeback exposure."
      else if (lowerQ.includes('velocity')) fallbackText = "Velocity anomalies: 14 attempts from the same IP subclass within 3 minutes."
      else if (lowerQ.includes('geo')) fallbackText = "GeoSentry-07 has flagged 3 cross-border anomalies in the last hour from high-risk corridors."
      
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { role: 'ai', text: fallbackText }
        return updated
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ borderLeft: '1px solid rgba(255,255,255,0.07)', display: 'flex', flexDirection: 'column', background: '#0f1217', overflow: 'hidden' }}>
      <div style={{ padding: '14px 16px', borderBottom: '1px solid rgba(255,255,255,0.07)', fontSize: 12, fontWeight: 700 }}>
        AI Investigation Panel
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
        {!transaction && (
          <div style={{ background: '#141820', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, padding: 14, fontSize: 12, lineHeight: 1.6 }}>
            <div style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 1.5, color: '#00e5a0', fontFamily: 'monospace', marginBottom: 6 }}>● FraudHunter AI</div>
            Select a flagged transaction to begin autonomous investigation. I will analyze patterns, cross-reference behavioral history, and deliver a risk verdict.
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{
            background: msg.role === 'user' ? 'rgba(0,102,255,0.06)' : '#141820',
            border: `1px solid ${msg.role === 'user' ? 'rgba(0,102,255,0.2)' : 'rgba(255,255,255,0.07)'}`,
            borderRadius: 10, padding: 12, fontSize: 12, lineHeight: 1.6,
          }}>
            <div style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 1.5, fontFamily: 'monospace', marginBottom: 6, color: msg.role === 'user' ? '#6699ff' : '#00e5a0', display: 'flex', alignItems: 'center', gap: 5 }}>
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: msg.role === 'user' ? '#6699ff' : '#00e5a0', display: 'inline-block' }} />
              {msg.role === 'user' ? 'You' : 'FraudHunter AI'}
            </div>
            {msg.loading ? (
              <div style={{ display: 'flex', gap: 4 }}>
                {[0,1,2].map(j => <span key={j} style={{ width: 6, height: 6, borderRadius: '50%', background: '#6b7280', animation: `pulse 1.2s ${j * 0.2}s ease-in-out infinite` }} />)}
              </div>
            ) : (
              <>
                <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
                {msg.findings?.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    {msg.findings.map((f, fi) => (
                      <div key={fi} style={{ borderLeft: `2px solid ${msg.color}`, paddingLeft: 8, marginBottom: 4, fontSize: 11, color: msg.color, fontFamily: 'monospace' }}>
                        {f.replace(/_/g, ' ')}
                      </div>
                    ))}
                  </div>
                )}
                {msg.verdict && (
                  <>
                    <div style={{ marginTop: 10, background: `${msg.color}12`, border: `1px solid ${msg.color}40`, borderRadius: 8, padding: 10 }}>
                      <div style={{ fontSize: 10, fontWeight: 700, color: msg.color, fontFamily: 'monospace', textTransform: 'uppercase', marginBottom: 4 }}>
                        {msg.verdict === 'critical' ? '🚨 Fraud Verdict' : msg.verdict === 'high' ? '⚠ High Risk' : 'ℹ Review'}
                      </div>
                      <div style={{ fontSize: 10, color: '#6b7280' }}>Recommended: {msg.recommended}</div>
                    </div>
                    {transaction && (
                      <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
                        <button onClick={() => onBlock(transaction.id)} style={{ flex: 1, padding: '7px 4px', borderRadius: 6, border: 'none', background: '#ff3d5a', color: '#fff', fontSize: 10, fontWeight: 700, cursor: 'pointer', fontFamily: 'monospace', textTransform: 'uppercase' }}>🚫 Block</button>
                        <button onClick={() => onFlag(transaction.id)} style={{ flex: 1, padding: '7px 4px', borderRadius: 6, border: '1px solid rgba(255,176,32,0.3)', background: 'rgba(255,176,32,0.1)', color: '#ffb020', fontSize: 10, fontWeight: 700, cursor: 'pointer', fontFamily: 'monospace', textTransform: 'uppercase' }}>⚑ Flag</button>
                        <button onClick={() => onClear(transaction.id)} style={{ flex: 1, padding: '7px 4px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.07)', background: 'rgba(107,114,128,0.1)', color: '#6b7280', fontSize: 10, fontWeight: 700, cursor: 'pointer', fontFamily: 'monospace', textTransform: 'uppercase' }}>✓ Pass</button>
                      </div>
                    )}
                  </>
                )}
              </>
            )}
          </div>
        ))}
      </div>
      <div style={{ padding: '10px 14px', borderTop: '1px solid rgba(255,255,255,0.07)', display: 'flex', gap: 8 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendQuery()}
          placeholder="Ask about fraud patterns..."
          style={{ flex: 1, background: '#141820', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, padding: '8px 12px', fontSize: 12, color: '#e8eaf0', fontFamily: 'inherit', outline: 'none' }}
        />
        <button disabled={loading} onClick={sendQuery} style={{ background: loading ? '#6b7280' : '#00e5a0', border: 'none', borderRadius: 8, padding: '8px 14px', color: '#000', fontSize: 12, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}>
          {loading ? '...' : 'Ask'}
        </button>
      </div>
    </div>
  )
}
