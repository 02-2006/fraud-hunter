// AnalyticsPage.jsx
import { useEffect, useState } from 'react'
import { api } from '../services/api'

export default function AnalyticsPage() {
  const [patterns, setPatterns] = useState([])
  const [dist, setDist] = useState(null)
  const [ts, setTs] = useState([])

  useEffect(() => {
    api.getTopPatterns().then(setPatterns).catch(console.error)
    api.getRiskDistribution().then(setDist).catch(console.error)
    api.getTimeSeries('fraud_count', 24).then(d => setTs(d.data || [])).catch(console.error)
  }, [])

  const maxVal = Math.max(...ts.map(p => p.value), 1)

  return (
    <div style={{ padding: 24, color: '#e8eaf0' }}>
      <h2 style={{ fontSize: 20, fontWeight: 800, marginBottom: 24 }}>Analytics & Insights</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        {/* Top fraud patterns */}
        <div style={{ background: '#0f1217', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 16 }}>Top Fraud Patterns</div>
          {patterns.map(p => (
            <div key={p.pattern} style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12 }}>
                <span>{p.pattern}</span>
                <span style={{ fontFamily: 'monospace', color: '#6b7280' }}>{p.count} ({p.pct}%)</span>
              </div>
              <div style={{ height: 4, background: 'rgba(255,255,255,0.07)', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${p.pct}%`, background: '#00e5a0', borderRadius: 2 }} />
              </div>
            </div>
          ))}
        </div>

        {/* Risk distribution */}
        {dist && (
          <div style={{ background: '#0f1217', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 16 }}>Risk Distribution</div>
            {[
              { key: 'critical', label: 'Critical', color: '#ff3d5a' },
              { key: 'high', label: 'High', color: '#ffb020' },
              { key: 'medium', label: 'Medium', color: '#6699ff' },
              { key: 'low', label: 'Low', color: '#6b7280' },
              { key: 'clear', label: 'Clear', color: '#00e5a0' },
            ].map(r => {
              const total = Object.values(dist).reduce((a, b) => a + b, 0)
              const pct = ((dist[r.key] / total) * 100).toFixed(1)
              return (
                <div key={r.key} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                  <span style={{ width: 60, fontSize: 11, color: r.color }}>{r.label}</span>
                  <div style={{ flex: 1, height: 4, background: 'rgba(255,255,255,0.07)', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: r.color, borderRadius: 2 }} />
                  </div>
                  <span style={{ fontSize: 11, fontFamily: 'monospace', color: '#6b7280', minWidth: 40 }}>{dist[r.key]}</span>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Time series sparkline */}
      <div style={{ background: '#0f1217', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 16 }}>Fraud Flags — Last 24 Hours</div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 80 }}>
          {ts.slice(-48).map((p, i) => (
            <div key={i} style={{ flex: 1, height: `${(p.value / maxVal) * 100}%`, minHeight: 2, background: p.value > 10 ? '#ff3d5a' : p.value > 5 ? '#ffb020' : '#00e5a0', borderRadius: '2px 2px 0 0', opacity: 0.8 }} />
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 10, color: '#6b7280', fontFamily: 'monospace' }}>
          <span>24h ago</span><span>12h ago</span><span>now</span>
        </div>
      </div>
    </div>
  )
}
