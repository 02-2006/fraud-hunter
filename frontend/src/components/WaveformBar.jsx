import { useEffect, useState } from 'react'

export default function WaveformBar() {
  const [bars, setBars] = useState([])
  useEffect(() => {
    function gen() {
      return Array.from({ length: 60 }, () => {
        const r = Math.random()
        const h = 8 + Math.random() * 48
        return { h, type: r < 0.05 ? 'alert' : r < 0.12 ? 'warn' : 'normal' }
      })
    }
    setBars(gen())
    const interval = setInterval(() => setBars(gen()), 1100)
    return () => clearInterval(interval)
  }, [])
  const colors = { alert: '#ff3d5a', warn: '#ffb020', normal: 'rgba(0,229,160,0.4)' }
  return (
    <div style={{ padding: '12px 20px', borderBottom: '1px solid rgba(255,255,255,0.07)', background: '#0f1217', flexShrink: 0 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <span style={{ fontSize: 12, fontWeight: 700 }}>Live Transaction Stream</span>
        <span style={{ fontSize: 10, color: '#6b7280', fontFamily: 'monospace' }}>4,821 tx/min</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, height: 56, overflow: 'hidden' }}>
        {bars.map((b, i) => (
          <div key={i} style={{ flex: 1, minWidth: 3, maxWidth: 8, height: b.h, background: colors[b.type], borderRadius: '2px 2px 0 0', transition: 'height 0.4s ease' }} />
        ))}
      </div>
    </div>
  )
}
