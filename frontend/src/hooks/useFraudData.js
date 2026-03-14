/**
 * useFraudData — polls backend for live transaction and agent data
 */
import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'

const POLL_INTERVAL_MS = 5000

export function useFraudData() {
  const [transactions, setTransactions] = useState([])
  const [agents, setAgents] = useState([])
  const [stats, setStats] = useState(null)
  const [patterns, setPatterns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAll = useCallback(async () => {
    try {
      const [txList, agentList, dashStats, topPatterns] = await Promise.allSettled([
        api.listTransactions({ limit: 50 }),
        api.listAgents(),
        api.getDashboardStats(),
        api.getTopPatterns(),
      ])
      if (txList.status === 'fulfilled') setTransactions(txList.value)
      if (agentList.status === 'fulfilled') setAgents(agentList.value)
      if (dashStats.status === 'fulfilled') setStats(dashStats.value)
      if (topPatterns.status === 'fulfilled') setPatterns(topPatterns.value)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [fetchAll])

  const blockTransaction = useCallback(async (id, reason) => {
    await api.decideTransaction(id, 'blocked', reason)
    setTransactions(prev =>
      prev.map(tx => tx.id === id ? { ...tx, status: 'blocked' } : tx)
    )
  }, [])

  const flagTransaction = useCallback(async (id) => {
    await api.decideTransaction(id, 'flagged')
    setTransactions(prev =>
      prev.map(tx => tx.id === id ? { ...tx, status: 'flagged' } : tx)
    )
  }, [])

  const clearTransaction = useCallback(async (id) => {
    await api.decideTransaction(id, 'cleared')
    setTransactions(prev =>
      prev.map(tx => tx.id === id ? { ...tx, status: 'cleared' } : tx)
    )
  }, [])

  const investigate = useCallback(async (transactionId, query) => {
    return api.investigateTransaction(transactionId, query)
  }, [])

  return {
    transactions, agents, stats, patterns,
    loading, error,
    blockTransaction, flagTransaction, clearTransaction, investigate,
    refresh: fetchAll,
  }
}
