import { useState } from 'react'

const NAV = [
  { key: 'dashboard', label: 'Dashboard', icon: 'D' },
  { key: 'investigation', label: 'Investigate', icon: 'I' },
  { key: 'analytics', label: 'Analytics', icon: 'A' },
  { key: 'cases', label: 'Cases', icon: 'C' },
]

export default function Sidebar({ activePage, onNavigate, connectionStatus }) {
  const statusColor = connectionStatus === 'connected' ? '#00e5a0' : '#ff3d5a'
  return (
    <div style={{ width: 64, background: '#0a0c0f', borderRight: '1px solid rgba(255,255,255,0.07)', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px 0', gap: 8 }}>
      <div style={{ width: 36, height: 36, background: '#00e5a0', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 14, marginBottom: 16, color: '#000' }}>FH</div>
      {NAV.map(n => (
        <button key={n.key} onClick={() => onNavigate(n.key)} title={n.label} style={{ width: 44, height: 44, borderRadius: 10, border: activePage === n.key ? '1px solid rgba(0,229,160,0.4)' : '1px solid rgba(255,255,255,0.07)', background: activePage === n.key ? 'rgba(0,229,160,0.1)' : 'transparent', color: activePage === n.key ? '#00e5a0' : '#6b7280', fontSize: 13, fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'inherit' }}>
          {n.icon}
        </button>
      ))}
      <div style={{ flex: 1 }} />
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: statusColor }} />
    </div>
  )
}
