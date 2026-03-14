// StatCard.jsx
export default function StatCard({ label, value, color = '#e8eaf0' }) {
  return (
    <div style={{ background: '#141820', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, padding: '10px 16px', minWidth: 100, flex: 1 }}>
      <div style={{ fontSize: 20, fontWeight: 800, fontFamily: 'monospace', color }}>{value}</div>
      <div style={{ fontSize: 10, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1, marginTop: 2 }}>{label}</div>
    </div>
  )
}
