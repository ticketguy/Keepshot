import { useEffect, useRef, useState, useCallback } from 'react'
import { notificationsApi } from '../api/client'
import { useAuthStore } from '../store/auth'

/**
 * Connects to the WebSocket for real-time notifications and
 * exposes the unread count + recent notification list.
 *
 * Falls back to polling every 30s when the WS is unavailable.
 */
export function useNotifications() {
  const { token, userId } = useAuthStore()
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const wsRef = useRef(null)

  const fetchNotifications = useCallback(async () => {
    if (!token) return
    try {
      const { data } = await notificationsApi.list({ page: 1, page_size: 20 })
      setNotifications(data.items || [])
      setUnreadCount((data.items || []).filter((n) => !n.read).length)
    } catch (_) {}
  }, [token])

  // Connect WebSocket
  useEffect(() => {
    if (!token || !userId) return

    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = window.location.host
    const url = `${proto}://${host}/ws/${userId}?token=${token}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        if (msg.type === 'notification') {
          setNotifications((prev) => [msg.data, ...prev].slice(0, 50))
          setUnreadCount((c) => c + 1)
        }
      } catch (_) {}
    }

    ws.onerror = () => ws.close()

    return () => ws.close()
  }, [token, userId])

  // Initial fetch + poll every 30s
  useEffect(() => {
    fetchNotifications()
    const id = setInterval(fetchNotifications, 30_000)
    return () => clearInterval(id)
  }, [fetchNotifications])

  const markRead = useCallback(async (id) => {
    await notificationsApi.markRead(id)
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    )
    setUnreadCount((c) => Math.max(0, c - 1))
  }, [])

  const markAllRead = useCallback(async () => {
    await notificationsApi.markAllRead()
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
    setUnreadCount(0)
  }, [])

  const dismiss = useCallback(async (id) => {
    await notificationsApi.delete(id)
    setNotifications((prev) => {
      const removed = prev.find((n) => n.id === id)
      if (removed && !removed.read) setUnreadCount((c) => Math.max(0, c - 1))
      return prev.filter((n) => n.id !== id)
    })
  }, [])

  return { notifications, unreadCount, markRead, markAllRead, dismiss, refetch: fetchNotifications }
}
