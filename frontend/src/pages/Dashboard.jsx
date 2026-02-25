import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bookmark,
  Radio,
  TrendingUp,
  Bell,
  ArrowRight,
  Globe,
  FileText,
  Image,
  FileImage,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { bookmarksApi, notificationsApi } from '../api/client'

const CONTENT_ICONS = {
  url: Globe,
  text: FileText,
  image: Image,
  pdf: FileImage,
}

function StatCard({ icon: Icon, label, value, accent = 'indigo', loading }) {
  const accents = {
    indigo: 'bg-indigo-500/10 text-indigo-400',
    emerald: 'bg-emerald-500/10 text-emerald-400',
    amber: 'bg-amber-500/10 text-amber-400',
    violet: 'bg-violet-500/10 text-violet-400',
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 flex items-center gap-4">
      <div className={`flex h-10 w-10 items-center justify-center rounded-lg flex-shrink-0 ${accents[accent]}`}>
        <Icon size={18} strokeWidth={1.75} />
      </div>
      <div>
        <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider">{label}</p>
        {loading ? (
          <div className="mt-1 h-6 w-10 animate-pulse rounded bg-zinc-800" />
        ) : (
          <p className="mt-0.5 text-2xl font-bold text-zinc-100">{value ?? '—'}</p>
        )}
      </div>
    </div>
  )
}

function ActivityItem({ notification }) {
  const Icon = CONTENT_ICONS.url

  return (
    <div className="flex items-start gap-3 py-3">
      <div className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-indigo-500/10">
        <Icon size={13} className="text-indigo-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-zinc-200 truncate">{notification.title}</p>
        <p className="mt-0.5 text-xs text-zinc-500 line-clamp-1">{notification.message}</p>
      </div>
      <span className="flex-shrink-0 text-xs text-zinc-600">
        {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
      </span>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState({ total: null, monitoring: null, unread: null })
  const [recentActivity, setRecentActivity] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const [bookRes, notifRes] = await Promise.all([
          bookmarksApi.list({ page: 1, page_size: 100 }),
          notificationsApi.list({ page: 1, page_size: 10 }),
        ])

        const bookmarks = bookRes.data.items || []
        const monitoring = bookmarks.filter((b) => b.monitoring_enabled).length
        const unread = (notifRes.data.items || []).filter((n) => !n.read).length

        setStats({ total: bookRes.data.total, monitoring, unread })
        setRecentActivity(notifRes.data.items?.slice(0, 8) || [])
      } catch (_) {
        setStats({ total: 0, monitoring: 0, unread: 0 })
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  return (
    <div className="max-w-4xl space-y-8">
      {/* Stats */}
      <section>
        <h2 className="mb-4 text-xs font-semibold uppercase tracking-widest text-zinc-500">
          Overview
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard
            icon={Bookmark}
            label="Bookmarks"
            value={stats.total}
            accent="indigo"
            loading={loading}
          />
          <StatCard
            icon={Radio}
            label="Monitoring"
            value={stats.monitoring}
            accent="emerald"
            loading={loading}
          />
          <StatCard
            icon={Bell}
            label="Unread alerts"
            value={stats.unread}
            accent="amber"
            loading={loading}
          />
          <StatCard
            icon={TrendingUp}
            label="Active today"
            value={loading ? null : recentActivity.filter((n) => {
              const d = new Date(n.created_at)
              return Date.now() - d.getTime() < 86_400_000
            }).length}
            accent="violet"
            loading={loading}
          />
        </div>
      </section>

      {/* Recent Activity */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
            Recent Activity
          </h2>
          <Link
            to="/bookmarks"
            className="flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            All bookmarks
            <ArrowRight size={12} />
          </Link>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 divide-y divide-zinc-800/60 px-5">
          {loading ? (
            <div className="space-y-3 py-5">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="h-7 w-7 animate-pulse rounded-lg bg-zinc-800" />
                  <div className="flex-1 space-y-1.5">
                    <div className="h-3.5 w-1/2 animate-pulse rounded bg-zinc-800" />
                    <div className="h-3 w-3/4 animate-pulse rounded bg-zinc-800/60" />
                  </div>
                </div>
              ))}
            </div>
          ) : recentActivity.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-12 text-zinc-600">
              <Bell size={28} strokeWidth={1.5} />
              <p className="text-sm">No activity yet — add your first bookmark</p>
              <Link
                to="/bookmarks"
                className="mt-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                Go to Bookmarks →
              </Link>
            </div>
          ) : (
            recentActivity.map((n) => (
              <ActivityItem key={n.id} notification={n} />
            ))
          )}
        </div>
      </section>
    </div>
  )
}
