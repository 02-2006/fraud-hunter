// AgentPanel.jsx
export function AgentPanel({ agents }) {
  return (
    <div style={{ padding: 16, borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
      <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 2, color: '#6b7280', marginBottom: 12, fontFamily: 'monospace' }}>Active Agents</div>
      {agents.map(agent => {
        const isRunning = agent.status === 'running'
        const hasAlert = agent.flags_raised > 50
        const pct = isRunning ? Math.min(90, Math.round(agent.transactions_scanned / 600)) : 100
        return (
          <div key={agent.agent_id} style={{ background: '#141820', border: `1px solid ${hasAlert && isRunning ? 'rgba(255,61,90,0.3)' : isRunning ? 'rgba(0,229,160,0.2)' : 'rgba(255,255,255,0.07)'}`, borderRadius: 10, padding: 12, marginBottom: 8, cursor: 'pointer' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 700 }}>{agent.agent_id}</span>
              <span style={{ fontSize: 9, padding: '2px 8px', borderRadius: 20, fontFamily: 'monospace', textTransform: 'uppercase', background: isRunning ? (hasAlert ? 'rgba(255,61,90,0.1)' : 'rgba(0,229,160,0.1)') : 'rgba(107,114,128,0.1)', color: isRunning ? (hasAlert ? '#ff3d5a' : '#00e5a0') : '#6b7280', border: `1px solid ${isRunning ? (hasAlert ? 'rgba(255,61,90,0.3)' : 'rgba(0,229,160,0.3)') : 'rgba(107,114,128,0.3)'}` }}>
                {isRunning ? (hasAlert ? 'Alert' : 'Scanning') : 'Idle'}
              </span>
            </div>
            <div style={{ height: 3, background: 'rgba(255,255,255,0.07)', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${pct}%`, background: isRunning ? (hasAlert ? '#ff3d5a' : '#00e5a0') : '#6b7280', borderRadius: 2 }} />
            </div>
            <div style={{ fontSize: 10, color: '#6b7280', fontFamily: 'monospace', marginTop: 5 }}>
              {agent.transactions_scanned.toLocaleString()} scanned · {agent.flags_raised} flagged
            </div>
          </div>
        )
      })}
    </div>
  )
}

// WaveformBar.jsx
import { useEffect, useState } from 'react'

export function WaveformBar() {
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

// Sidebar.jsx
const NAV = [
  { key: 'dashboard', label: 'Dashboard', icon: '◉' },
  { key: 'investigation', label: 'Investigate', icon: '◎' },
  { key: 'analytics', label: 'Analytics', icon: '▣' },
  { key: 'cases', label: 'Cases', icon: '⬡' },
]

export function Sidebar({ activePage, onNavigate, connectionStatus, alerts }) {
  const statusColor = connectionStatus === 'connected' ? '#00e5a0' : connectionStatus === 'disconnected' ? '#ff3d5a' : '#ffb020'

  return (
    <div style={{ width: 64, background: '#0a0c0f', borderRight: '1px solid rgba(255,255,255,0.07)', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px 0', gap: 8 }}>
      <div style={{ width: 36, height: 36, background: 'linear-gradient(135deg,#00e5a0,#00b37a)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, marginBottom: 16 }}>🛡</div>
      {NAV.map(n => (
        <button key={n.key} onClick={() => onNavigate(n.key)} title={n.label} style={{ width: 44, height: 44, borderRadius: 10, border: `1px solid ${activePage === n.key ? 'rgba(0,229,160,0.4)' : 'rgba(255,255,255,0.07)'}`, background: activePage === n.key ? 'rgba(0,229,160,0.1)' : 'transparent', color: activePage === n.key ? '#00e5a0' : '#6b7280', fontSize: 16, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {n.icon}
        </button>
      ))}
      <div style={{ flex: 1 }} />
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: statusColor }} title={connectionStatus} />
    </div>
  )
}

export default AgentPanel
