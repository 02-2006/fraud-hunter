/**
 * useWebSocket — real-time connection to the transaction stream
 */
import { useState, useEffect, useRef, useCallback } from 'react'

const RECONNECT_DELAY_MS = 3000
const MAX_RECONNECT_ATTEMPTS = 10

export function useWebSocket(url) {
  const [lastMessage, setLastMessage] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const ws = useRef(null)
  const reconnectCount = useRef(0)
  const reconnectTimer = useRef(null)

  const connect = useCallback(() => {
    if (!url) return
    try {
      ws.current = new WebSocket(url)

      ws.current.onopen = () => {
        setConnectionStatus('connected')
        reconnectCount.current = 0
        console.info('[WS] Connected to stream')
      }

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
        } catch {
          // non-JSON message, ignore
        }
      }

      ws.current.onclose = () => {
        setConnectionStatus('disconnected')
        if (reconnectCount.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectCount.current++
          console.warn(`[WS] Disconnected. Reconnecting in ${RECONNECT_DELAY_MS}ms... (attempt ${reconnectCount.current})`)
          reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS)
        } else {
          setConnectionStatus('failed')
          console.error('[WS] Max reconnect attempts reached.')
        }
      }

      ws.current.onerror = (err) => {
        console.error('[WS] Error:', err)
        setConnectionStatus('error')
      }
    } catch (err) {
      console.error('[WS] Failed to create WebSocket:', err)
      setConnectionStatus('error')
    }
  }, [url])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      ws.current?.close()
    }
  }, [connect])

  const sendMessage = useCallback((data) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }, [])

  return { lastMessage, connectionStatus, sendMessage }
}
