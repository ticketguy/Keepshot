import { X, BellOff, Check, CheckCheck, Trash2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const TYPE_STYLES = {
  content_changed: 'bg-amber-500/10 text-amber-400',
  significant_change: 'bg-rose-500/10 text-rose-400',
  price_change: 'bg-emerald-500/10 text-emerald-400',
  default: 'bg-indigo-500/10 text-indigo-400',
}

export default function NotificationPanel({
  open,
  onClose,
  notifications = [],
  onMarkRead,
  onMarkAllRead,
  onDismiss,
}) {
  const unreadCount = notifications.filter((n) => !n.read).length

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
          onClick={onClose}
        />
      )}

      {/* Panel */}
      <aside
        className={`fixed inset-y-0 right-0 z-50 flex w-96 flex-col border-l border-zinc-800 bg-zinc-950 shadow-2xl transition-transform duration-200 ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-zinc-800 px-5 py-4">
          <div className="flex items-center gap-2">
            <h2 className="font-semibold text-zinc-100">Notifications</h2>
            {unreadCount > 0 && (
              <span className="rounded-full bg-indigo-500/20 px-2 py-0.5 text-xs font-medium text-indigo-400">
                {unreadCount} new
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            {unreadCount > 0 && (
              <button
                onClick={onMarkAllRead}
                title="Mark all as read"
                className="flex h-8 w-8 items-center justify-center rounded-lg text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
              >
                <CheckCheck size={16} />
              </button>
            )}
            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 py-20 text-zinc-600">
              <BellOff size={32} strokeWidth={1.5} />
              <p className="text-sm">No notifications yet</p>
            </div>
          ) : (
            <ul className="divide-y divide-zinc-800/60">
              {notifications.map((n) => (
                <li
                  key={n.id}
                  className={`group flex gap-3 px-5 py-3.5 transition-colors hover:bg-zinc-900/60 ${
                    !n.read ? 'bg-indigo-500/[0.03]' : ''
                  }`}
                >
                  {/* Dot */}
                  <div className="mt-1 flex-shrink-0">
                    {!n.read ? (
                      <span className="block h-2 w-2 rounded-full bg-indigo-400" />
                    ) : (
                      <span className="block h-2 w-2 rounded-full bg-zinc-700" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-200 truncate">{n.title}</p>
                    <p className="mt-0.5 text-xs text-zinc-400 line-clamp-2">{n.message}</p>
                    <div className="mt-1.5 flex items-center gap-2">
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                          TYPE_STYLES[n.notification_type] ?? TYPE_STYLES.default
                        }`}
                      >
                        {n.notification_type?.replace(/_/g, ' ')}
                      </span>
                      <span className="text-[11px] text-zinc-600">
                        {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-shrink-0 flex-col items-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {!n.read && (
                      <button
                        onClick={() => onMarkRead(n.id)}
                        title="Mark as read"
                        className="flex h-6 w-6 items-center justify-center rounded text-zinc-500 hover:text-emerald-400 transition-colors"
                      >
                        <Check size={13} />
                      </button>
                    )}
                    <button
                      onClick={() => onDismiss(n.id)}
                      title="Dismiss"
                      className="flex h-6 w-6 items-center justify-center rounded text-zinc-500 hover:text-rose-400 transition-colors"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
    </>
  )
}
