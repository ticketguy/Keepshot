import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import NotificationPanel from '../NotificationPanel'
import { useNotifications } from '../../hooks/useNotifications'

const PAGE_TITLES = {
  '/dashboard': 'Dashboard',
  '/bookmarks': 'Bookmarks',
}

export default function Layout() {
  const { pathname } = useLocation()
  const [notifOpen, setNotifOpen] = useState(false)
  const notif = useNotifications()

  return (
    <div className="flex min-h-screen bg-zinc-950">
      <Sidebar />

      <div className="flex flex-1 flex-col pl-60">
        <Header
          title={PAGE_TITLES[pathname] ?? 'KeepShot'}
          unreadCount={notif.unreadCount}
          onNotificationClick={() => setNotifOpen(true)}
        />

        <main className="flex-1 p-6 animate-fade-in">
          <Outlet />
        </main>
      </div>

      <NotificationPanel
        open={notifOpen}
        onClose={() => setNotifOpen(false)}
        notifications={notif.notifications}
        onMarkRead={notif.markRead}
        onMarkAllRead={notif.markAllRead}
        onDismiss={notif.dismiss}
      />
    </div>
  )
}
