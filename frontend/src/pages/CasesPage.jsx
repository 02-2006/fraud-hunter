// CasesPage.jsx
import { useState } from 'react'
import { api } from '../services/api'

const MOCK_CASES = [
  { id: '1', case_number: 'FH-20260314-A1B2C3', account_id: 'ACC-99221', status: 'investigating', total_exposure: 28400, fraud_type: 'Card Sharing Ring', created_at: '2026-03-14T01:22:00Z' },
  { id: '2', case_number: 'FH-20260314-D4E5F6', account_id: 'ACC-44102', status: 'open', total_exposure: 12800, fraud_type: 'Account Takeover', created_at: '2026-03-14T02:45:00Z' },
  { id: '3', case_number: 'FH-20260313-G7H8I9', account_id: 'ACC-77331', status: 'escalated', total_exposure: 87200, fraud_type: 'Synthetic Identity Ring', created_at: '2026-03-13T18:10:00Z' },
  { id: '4', case_number: 'FH-20260313-J1K2L3', account_id: 'ACC-55890', status: 'resolved', total_exposure: 4100, fraud_type: 'Velocity Burst', created_at: '2026-03-13T09:30:00Z' },
]

const STATUS_COLORS = { open: '#6699ff', investigating: '#ffb020', escalated: '#ff3d5a', resolved: '#00e5a0' }

export default function CasesPage() {
  const [cases, setCases] = useState(MOCK_CASES)

  async function escalate(id) {
    setCases(prev => prev.map(c => c.id === id ? { ...c, status: 'escalated' } : c))
  }

  return (
    <div style={{ padding: 24, color: '#e8eaf0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ fontSize: 20, fontWeight: 800 }}>Fraud Cases</h2>
        <div style={{ display: 'flex', gap: 8, fontSize: 11, fontFamily: 'monospace' }}>
          {['All', 'Open', 'Investigating', 'Escalated'].map(s => (
            <button key={s} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)', background: 'transparent', color: '#6b7280', cursor: 'pointer', fontFamily: 'inherit', fontSize: 11 }}>{s}</button>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {cases.map(c => (
          <div key={c.id} style={{ background: '#0f1217', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: '16px 20px', display: 'grid', gridTemplateColumns: '1fr auto auto auto', gap: 20, alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, fontFamily: 'monospace', marginBottom: 4 }}>{c.case_number}</div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>{c.fraud_type} · Account {c.account_id}</div>
              <div style={{ fontSize: 10, color: '#6b7280', marginTop: 4, fontFamily: 'monospace' }}>{new Date(c.created_at).toLocaleString()}</div>
            </div>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, fontFamily: 'monospace', color: '#ff3d5a' }}>${c.total_exposure.toLocaleString()}</div>
              <div style={{ fontSize: 10, color: '#6b7280' }}>Exposure</div>
            </div>
            <span style={{ fontSize: 10, padding: '4px 10px', borderRadius: 20, textTransform: 'uppercase', fontFamily: 'monospace', background: `${STATUS_COLORS[c.status]}15`, color: STATUS_COLORS[c.status], border: `1px solid ${STATUS_COLORS[c.status]}40` }}>
              {c.status}
            </span>
            <button onClick={() => escalate(c.id)} style={{ padding: '7px 14px', borderRadius: 6, border: '1px solid rgba(255,61,90,0.3)', background: 'rgba(255,61,90,0.08)', color: '#ff3d5a', fontSize: 11, cursor: 'pointer', fontFamily: 'monospace', textTransform: 'uppercase', fontWeight: 700 }}>
              Escalate
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
