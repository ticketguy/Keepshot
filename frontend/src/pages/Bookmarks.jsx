import { useEffect, useState, useCallback } from 'react'
import {
  Globe,
  FileText,
  Image,
  FileImage,
  Film,
  Plus,
  Search,
  ToggleLeft,
  ToggleRight,
  Trash2,
  RefreshCw,
  X,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { bookmarksApi } from '../api/client'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'

// ── Helpers ───────────────────────────────────────────────────────────────────

const CONTENT_META = {
  url: { icon: Globe, label: 'URL', preset: 'url' },
  text: { icon: FileText, label: 'Text', preset: 'text' },
  image: { icon: Image, label: 'Image', preset: 'image' },
  pdf: { icon: FileImage, label: 'PDF', preset: 'pdf' },
  video: { icon: Film, label: 'Video', preset: 'url' },
}

function getMeta(type) {
  return CONTENT_META[type] ?? { icon: Globe, label: type, preset: 'url' }
}

// ── Add Bookmark Modal ────────────────────────────────────────────────────────

function AddModal({ open, onClose, onCreated }) {
  const [form, setForm] = useState({
    content_type: 'url',
    url: '',
    title: '',
    raw_content: '',
    monitoring_enabled: true,
    check_interval: 60,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function set(field, val) {
    setForm((f) => ({ ...f, [field]: val }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = { ...form }
      if (form.content_type !== 'text') delete payload.raw_content
      if (form.content_type === 'text') delete payload.url
      await bookmarksApi.create(payload)
      onCreated()
      onClose()
      setForm({ content_type: 'url', url: '', title: '', raw_content: '', monitoring_enabled: true, check_interval: 60 })
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Failed to create bookmark')
    } finally {
      setLoading(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl animate-fade-in">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-semibold text-zinc-100">Add Bookmark</h2>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-200 transition-colors">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Content type */}
          <div className="flex gap-2">
            {Object.entries(CONTENT_META).map(([type, { label }]) => (
              <button
                key={type}
                type="button"
                onClick={() => set('content_type', type)}
                className={`flex-1 rounded-lg py-1.5 text-xs font-medium transition-colors border ${
                  form.content_type === type
                    ? 'bg-indigo-500/20 border-indigo-500/40 text-indigo-400'
                    : 'border-zinc-700 text-zinc-500 hover:border-zinc-500 hover:text-zinc-300'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <Input
            label="Title (optional)"
            placeholder="Give it a name"
            value={form.title}
            onChange={(e) => set('title', e.target.value)}
          />

          {form.content_type === 'text' ? (
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-zinc-300">Content</label>
              <textarea
                placeholder="Paste or type your text content…"
                value={form.raw_content}
                onChange={(e) => set('raw_content', e.target.value)}
                rows={4}
                className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500
                  focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none transition-colors"
              />
            </div>
          ) : (
            <Input
              label="URL"
              type="url"
              placeholder="https://example.com"
              value={form.url}
              onChange={(e) => set('url', e.target.value)}
            />
          )}

          <div className="flex items-center justify-between rounded-lg border border-zinc-800 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-zinc-200">Enable monitoring</p>
              <p className="text-xs text-zinc-500">Auto-check for changes</p>
            </div>
            <button
              type="button"
              onClick={() => set('monitoring_enabled', !form.monitoring_enabled)}
              className={`transition-colors ${form.monitoring_enabled ? 'text-indigo-400' : 'text-zinc-600'}`}
            >
              {form.monitoring_enabled ? <ToggleRight size={28} /> : <ToggleLeft size={28} />}
            </button>
          </div>

          {error && (
            <p className="rounded-lg bg-rose-500/10 border border-rose-500/20 px-3 py-2 text-sm text-rose-400">
              {error}
            </p>
          )}

          <div className="flex gap-2 pt-1">
            <Button type="button" variant="outline" className="flex-1" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" className="flex-1" loading={loading}>
              Add bookmark
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Bookmark Card ─────────────────────────────────────────────────────────────

function BookmarkCard({ bookmark, onToggleMonitor, onDelete }) {
  const meta = getMeta(bookmark.content_type)
  const Icon = meta.icon
  const [toggling, setToggling] = useState(false)
  const [deleting, setDeleting] = useState(false)

  async function handleToggle() {
    setToggling(true)
    try {
      await onToggleMonitor(bookmark.id, !bookmark.monitoring_enabled)
    } finally {
      setToggling(false)
    }
  }

  async function handleDelete() {
    if (!confirm('Remove this bookmark?')) return
    setDeleting(true)
    try {
      await onDelete(bookmark.id)
    } finally {
      setDeleting(false)
    }
  }

  const displayTitle =
    bookmark.title ||
    (bookmark.url ? new URL(bookmark.url).hostname.replace('www.', '') : 'Untitled')

  return (
    <div className="group flex items-center gap-4 rounded-xl border border-zinc-800 bg-zinc-900/50 px-5 py-4 transition-colors hover:border-zinc-700 hover:bg-zinc-900">
      {/* Icon */}
      <div
        className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg ${
          { url: 'bg-blue-500/10 text-blue-400',
            text: 'bg-violet-500/10 text-violet-400',
            image: 'bg-pink-500/10 text-pink-400',
            pdf: 'bg-orange-500/10 text-orange-400',
            video: 'bg-cyan-500/10 text-cyan-400' }[bookmark.content_type] ??
          'bg-zinc-800 text-zinc-400'
        }`}
      >
        <Icon size={16} strokeWidth={1.75} />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="truncate text-sm font-medium text-zinc-100">{displayTitle}</p>
          <Badge
            label={meta.label}
            preset={meta.preset}
          />
        </div>
        <p className="mt-0.5 truncate text-xs text-zinc-500">
          {bookmark.url ||
            bookmark.raw_content?.slice(0, 60) ||
            bookmark.description ||
            'No description'}
          {bookmark.raw_content?.length > 60 ? '…' : ''}
        </p>
      </div>

      {/* Monitoring badge */}
      <div className="flex-shrink-0">
        <Badge
          label={bookmark.monitoring_enabled ? 'Live' : 'Off'}
          preset={bookmark.monitoring_enabled ? 'live' : 'off'}
        />
      </div>

      {/* Last checked */}
      <p className="flex-shrink-0 text-xs text-zinc-600 w-20 text-right">
        {bookmark.last_checked_at
          ? formatDistanceToNow(new Date(bookmark.last_checked_at), { addSuffix: true })
          : 'Never'}
      </p>

      {/* Actions — visible on hover */}
      <div className="flex flex-shrink-0 items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={handleToggle}
          disabled={toggling}
          title={bookmark.monitoring_enabled ? 'Pause monitoring' : 'Enable monitoring'}
          className={`flex h-8 w-8 items-center justify-center rounded-lg transition-colors ${
            bookmark.monitoring_enabled
              ? 'text-indigo-400 hover:bg-indigo-500/10'
              : 'text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300'
          }`}
        >
          {toggling ? (
            <span className="h-3.5 w-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
          ) : bookmark.monitoring_enabled ? (
            <ToggleRight size={16} />
          ) : (
            <ToggleLeft size={16} />
          )}
        </button>

        <button
          onClick={handleDelete}
          disabled={deleting}
          title="Delete"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-zinc-600 hover:bg-rose-500/10 hover:text-rose-400 transition-colors"
        >
          {deleting ? (
            <span className="h-3.5 w-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
          ) : (
            <Trash2 size={14} />
          )}
        </button>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

const FILTERS = [
  { label: 'All', value: null },
  { label: 'URLs', value: 'url' },
  { label: 'Text', value: 'text' },
  { label: 'Images', value: 'image' },
  { label: 'PDFs', value: 'pdf' },
]

export default function Bookmarks() {
  const [bookmarks, setBookmarks] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState(null)
  const [addOpen, setAddOpen] = useState(false)
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 20

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, page_size: PAGE_SIZE }
      if (filter) params.content_type = filter
      const { data } = await bookmarksApi.list(params)
      setBookmarks(data.items || [])
      setTotal(data.total || 0)
    } catch (_) {
      setBookmarks([])
    } finally {
      setLoading(false)
    }
  }, [page, filter])

  useEffect(() => { load() }, [load])

  // Reset page when filter changes
  useEffect(() => { setPage(1) }, [filter])

  async function handleToggleMonitor(id, enabled) {
    await bookmarksApi.update(id, { monitoring_enabled: enabled })
    setBookmarks((prev) =>
      prev.map((b) => (b.id === id ? { ...b, monitoring_enabled: enabled } : b))
    )
  }

  async function handleDelete(id) {
    await bookmarksApi.delete(id)
    setBookmarks((prev) => prev.filter((b) => b.id !== id))
    setTotal((t) => t - 1)
  }

  // Client-side search filter
  const filtered = search.trim()
    ? bookmarks.filter(
        (b) =>
          b.title?.toLowerCase().includes(search.toLowerCase()) ||
          b.url?.toLowerCase().includes(search.toLowerCase()) ||
          b.raw_content?.toLowerCase().includes(search.toLowerCase())
      )
    : bookmarks

  return (
    <div className="max-w-4xl space-y-5">
      {/* Toolbar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        {/* Search */}
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
          <input
            type="search"
            placeholder="Search bookmarks…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-9 w-full rounded-lg border border-zinc-700 bg-zinc-900 pl-9 pr-3 text-sm text-zinc-100 placeholder:text-zinc-500
              focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors"
          />
        </div>

        <div className="flex items-center gap-2">
          {/* Filter tabs */}
          <div className="flex rounded-lg border border-zinc-800 bg-zinc-900 p-0.5 gap-0.5">
            {FILTERS.map(({ label, value }) => (
              <button
                key={label}
                onClick={() => setFilter(value)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                  filter === value
                    ? 'bg-indigo-500/20 text-indigo-400'
                    : 'text-zinc-500 hover:text-zinc-300'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <button
            onClick={load}
            title="Refresh"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-500 hover:text-zinc-200 hover:border-zinc-700 transition-colors"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>

          <Button onClick={() => setAddOpen(true)}>
            <Plus size={15} />
            Add
          </Button>
        </div>
      </div>

      {/* Count */}
      <p className="text-xs text-zinc-500">
        {loading ? 'Loading…' : `${total} bookmark${total !== 1 ? 's' : ''}${filter ? ` · filtered by ${filter}` : ''}`}
      </p>

      {/* List */}
      <div className="space-y-2">
        {loading ? (
          [...Array(5)].map((_, i) => (
            <div key={i} className="h-[72px] animate-pulse rounded-xl border border-zinc-800 bg-zinc-900/50" />
          ))
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900/30 py-16 text-zinc-600">
            <Globe size={32} strokeWidth={1.5} />
            <p className="text-sm">
              {search ? 'No bookmarks match your search' : 'No bookmarks yet'}
            </p>
            {!search && (
              <Button size="sm" variant="outline" onClick={() => setAddOpen(true)}>
                <Plus size={13} />
                Add your first bookmark
              </Button>
            )}
          </div>
        ) : (
          filtered.map((b) => (
            <BookmarkCard
              key={b.id}
              bookmark={b}
              onToggleMonitor={handleToggleMonitor}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>

      {/* Pagination */}
      {!loading && total > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <span className="text-xs text-zinc-500">
            Page {page} of {Math.ceil(total / PAGE_SIZE)}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page * PAGE_SIZE >= total}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}

      <AddModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        onCreated={load}
      />
    </div>
  )
}
