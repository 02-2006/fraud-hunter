const RISK_COLORS = { critical: '#ff3d5a', high: '#ffb020', medium: '#6699ff', low: '#6b7280', clear: '#00e5a0' }
const RISK_BG = { critical: 'rgba(255,61,90,0.1)', high: 'rgba(255,176,32,0.1)', medium: 'rgba(0,102,255,0.1)', low: 'rgba(107,114,128,0.1)', clear: 'rgba(0,229,160,0.1)' }

export default function TransactionFeed({ transactions, selectedId, onSelect }) {
  return (
    <div style={{ flex: 1, overflowY: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 20px', borderBottom: '1px solid rgba(255,255,255,0.07)', position: 'sticky', top: 0, background: '#0a0c0f', zIndex: 5 }}>
        <span style={{ fontSize: 13, fontWeight: 700 }}>Flagged Transactions</span>
        <span style={{ fontSize: 11, color: '#6b7280', fontFamily: 'monospace' }}>Showing {transactions.length} of 1,284</span>
      </div>
      {transactions.map(tx => (
        <div
          key={tx.id}
          onClick={() => onSelect(tx)}
          style={{
            display: 'grid', gridTemplateColumns: '38px 1fr auto 100px 80px', gap: 12, alignItems: 'center',
            padding: '11px 20px', borderBottom: '1px solid rgba(255,255,255,0.05)', cursor: 'pointer',
            background: selectedId === tx.id ? 'rgba(0,229,160,0.04)' : 'transparent',
            borderLeft: selectedId === tx.id ? '2px solid #00e5a0' : '2px solid transparent',
            transition: 'background 0.15s',
          }}
        >
          <div style={{
            width: 38, height: 38, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: RISK_BG[tx.risk_level], border: `1px solid ${RISK_COLORS[tx.risk_level]}30`,
            color: RISK_COLORS[tx.risk_level], fontWeight: 800, fontSize: 13, flexShrink: 0,
          }}>
            {tx.risk_level === 'critical' ? '!' : tx.risk_level === 'high' ? '▲' : '~'}
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 700, fontFamily: 'monospace', color: '#e8eaf0' }}>{tx.external_id}</div>
            <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {tx.merchant_name} · {tx.country_origin || 'XX'} · {tx.is_card_present ? 'Card present' : 'CNP'}
            </div>
          </div>
          <div style={{ fontSize: 11, color: '#6b7280', fontFamily: 'monospace', textAlign: 'right' }}>
            {tx.status}
          </div>
          <div style={{ fontSize: 14, fontWeight: 800, fontFamily: 'monospace', textAlign: 'right', color: RISK_COLORS[tx.risk_level] }}>
            ${tx.amount.toLocaleString()}
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 10, fontFamily: 'monospace', color: RISK_COLORS[tx.risk_level], textTransform: 'uppercase' }}>
              {tx.risk_level} {Math.round(tx.risk_score * 100)}
            </div>
            <div style={{ height: 4, background: 'rgba(255,255,255,0.07)', borderRadius: 2, marginTop: 4, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${tx.risk_score * 100}%`, background: RISK_COLORS[tx.risk_level], borderRadius: 2 }} />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
