import { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import InvestigationPage from './pages/InvestigationPage'
import AnalyticsPage from './pages/AnalyticsPage'
import CasesPage from './pages/CasesPage'
import Sidebar from './components/Sidebar'

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [connectionStatus] = useState('connected')

  const pages = { dashboard: Dashboard, investigation: InvestigationPage, analytics: AnalyticsPage, cases: CasesPage }
  const PageComponent = pages[page] || Dashboard

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0a0c0f', color: '#e8eaf0', overflow: 'hidden' }}>
      <Sidebar activePage={page} onNavigate={setPage} connectionStatus={connectionStatus} />
      <main style={{ flex: 1, overflow: 'auto' }}>
        <PageComponent />
      </main>
    </div>
  )
}
