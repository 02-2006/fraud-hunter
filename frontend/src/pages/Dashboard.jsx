import { useState } from 'react'
import StatCard from '../components/StatCard'
import TransactionFeed from '../components/TransactionFeed'
import AgentPanel from '../components/AgentPanel'
import InvestigationPanel from '../components/InvestigationPanel'
import WaveformBar from '../components/WaveformBar'
import { useFraudData } from '../hooks/useFraudData'

const MOCK_TRANSACTIONS = [
  { id: 'TXN-9921', external_id: 'TXN-9921', merchant_name: 'Crypto Exchange', amount: 12840, currency: 'USD', risk_level: 'critical', risk_score: 0.97, status: 'flagged', country_origin: 'NG', is_card_present: false, agent_findings: [{ agent_id: 'TxSweeper-01', rules_triggered: ['card_not_present_large', 'amount_over_10k'] }] },
  { id: 'TXN-9918', external_id: 'TXN-9918', merchant_name: 'Steam Gift Cards', amount: 3290, currency: 'USD', risk_level: 'critical', risk_score: 0.95, status: 'pending', country_origin: 'US', is_card_present: true, agent_findings: [{ agent_id: 'VelocityCheck-12', pattern: 'velocity_alert', count_1h: 42 }] },
  { id: 'TXN-9912', external_id: 'TXN-9912', merchant_name: 'Unknown Exchange', amount: 8100, currency: 'USD', risk_level: 'critical', risk_score: 0.91, status: 'pending', country_origin: 'RO', is_card_present: false, agent_findings: [{ agent_id: 'GeoSentry-07', pattern: 'geo_anomaly' }] },
  { id: 'TXN-9908', external_id: 'TXN-9908', merchant_name: 'iTunes Store', amount: 2750, currency: 'USD', risk_level: 'high', risk_score: 0.84, status: 'reviewing', country_origin: 'US', is_card_present: true, agent_findings: [] },
  { id: 'TXN-9901', external_id: 'TXN-9901', merchant_name: 'Booking.com', amount: 1920, currency: 'USD', risk_level: 'high', risk_score: 0.79, status: 'pending', country_origin: 'BG', is_card_present: false, agent_findings: [] },
  { id: 'TXN-9895', external_id: 'TXN-9895', merchant_name: 'PayPal Transfer', amount: 5400, currency: 'USD', risk_level: 'high', risk_score: 0.76, status: 'pending', country_origin: 'US', is_card_present: true, agent_findings: [] },
  { id: 'TXN-9882', external_id: 'TXN-9882', merchant_name: 'Walmart Online', amount: 630, currency: 'USD', risk_level: 'medium', risk_score: 0.58, status: 'pending', country_origin: 'US', is_card_present: true, agent_findings: [] },
  { id: 'TXN-9871', external_id: 'TXN-9871', merchant_name: 'Spotify', amount: 0.01, currency: 'USD', risk_level: 'medium', risk_score: 0.52, status: 'pending', country_origin: 'US', is_card_present: true, agent_findings: [] },
]

const MOCK_AGENTS = [
  { agent_id: 'TxSweeper-01', agent_type: 'tx_sweeper', status: 'running', transactions_scanned: 48210, flags_raised: 312, started_at: new Date().toISOString() },
  { agent_id: 'PatternNet-03', agent_type: 'pattern_net', status: 'running', transactions_scanned: 48210, flags_raised: 7, started_at: new Date().toISOString() },
  { agent_id: 'GeoSentry-07', agent_type: 'geo_sentry', status: 'running', transactions_scanned: 48210, flags_raised: 48, started_at: new Date().toISOString() },
  { agent_id: 'VelocityCheck-12', agent_type: 'velocity_check', status: 'stopped', transactions_scanned: 12800, flags_raised: 89, started_at: new Date().toISOString() },
]

export default function Dashboard({ stats }) {
  const [selectedTx, setSelectedTx] = useState(null)
  const [filter, setFilter] = useState('all')
  const { blockTransaction, flagTransaction, clearTransaction, investigate } = useFraudData()

  const displayStats = stats || {
    total_transactions: 1284321,
    flagged_today: 312,
    blocked_today: 142,
    critical_alerts: 7,
    total_exposure_blocked: 2847320.50,
    precision: 0.992,
    recall: 0.978,
    transactions_per_minute: 4821,
    active_agents: 3,
  }

  const filteredTx = filter === 'all'
    ? MOCK_TRANSACTIONS
    : MOCK_TRANSACTIONS.filter(t => t.risk_level === filter)

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr 320px', height: '100%' }}>
      {/* Left: Agents + Filters */}
      <div style={{ borderRight: '1px solid rgba(255,255,255,0.07)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <AgentPanel agents={MOCK_AGENTS} />
        <div style={{ padding: '16px', borderTop: '1px solid rgba(255,255,255,0.07)' }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 2, color: '#6b7280', marginBottom: 10, fontFamily: 'monospace' }}>Risk Filter</div>
          {[
            { key: 'all', label: 'All', count: '1,284' },
            { key: 'critical', label: 'Critical', count: '7', color: '#ff3d5a' },
            { key: 'high', label: 'High Risk', count: '23', color: '#ffb020' },
            { key: 'medium', label: 'Medium', count: '89', color: '#6699ff' },
          ].map(f => (
            <button key={f.key} onClick={() => setFilter(f.key)} style={{
              width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '8px 10px', marginBottom: 5, borderRadius: 6, cursor: 'pointer',
              background: filter === f.key ? 'rgba(0,229,160,0.05)' : 'transparent',
              border: `1px solid ${filter === f.key ? 'rgba(0,229,160,0.4)' : 'rgba(255,255,255,0.07)'}`,
              color: filter === f.key ? '#00e5a0' : '#e8eaf0', fontSize: 12, fontFamily: 'inherit',
            }}>
              <span>{f.label}</span>
              <span style={{ fontFamily: 'monospace', color: f.color || (filter === f.key ? '#00e5a0' : '#6b7280') }}>{f.count}</span>
            </button>
          ))}
        </div>
        <div style={{ padding: '16px', borderTop: '1px solid rgba(255,255,255,0.07)' }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 2, color: '#6b7280', marginBottom: 10, fontFamily: 'monospace' }}>Model Performance</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[
              { label: 'Precision', value: `${(displayStats.precision * 100).toFixed(1)}%`, color: '#00e5a0' },
              { label: 'Recall', value: `${(displayStats.recall * 100).toFixed(1)}%`, color: '#00e5a0' },
              { label: 'False Pos.', value: '0.8%', color: '#ffb020' },
              { label: 'Latency', value: '14ms', color: '#6699ff' },
            ].map(m => (
              <div key={m.label} style={{ background: '#141820', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, padding: 10 }}>
                <div style={{ fontSize: 16, fontWeight: 800, fontFamily: 'monospace', color: m.color }}>{m.value}</div>
                <div style={{ fontSize: 9, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1, marginTop: 2 }}>{m.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Center: Stream + Feed */}
      <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Stats bar */}
        <div style={{ display: 'flex', gap: 12, padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.07)', background: '#0f1217', flexShrink: 0 }}>
          <StatCard label="Critical" value={displayStats.critical_alerts} color="#ff3d5a" />
          <StatCard label="Flagged Today" value={displayStats.flagged_today} color="#ffb020" />
          <StatCard label="Blocked" value={displayStats.blocked_today} color="#00e5a0" />
          <StatCard label="Tx/min" value={Math.round(displayStats.transactions_per_minute).toLocaleString()} color="#6699ff" />
          <StatCard label="Exposure Blocked" value={`$${(displayStats.total_exposure_blocked / 1e6).toFixed(2)}M`} color="#00e5a0" />
        </div>

        {/* Waveform */}
        <WaveformBar />

        {/* Transaction feed */}
        <TransactionFeed
          transactions={filteredTx}
          selectedId={selectedTx?.id}
          onSelect={setSelectedTx}
        />
      </div>

      {/* Right: Investigation */}
      <InvestigationPanel
        transaction={selectedTx}
        onBlock={blockTransaction}
        onFlag={flagTransaction}
        onClear={clearTransaction}
        onInvestigate={investigate}
      />
    </div>
  )
}
