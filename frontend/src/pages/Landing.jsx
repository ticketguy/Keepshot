import { Link, Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { useTheme } from '../hooks/useTheme'
import {
  Bookmark,
  Bell,
  Zap,
  Eye,
  History,
  Globe,
  Moon,
  Sun,
  ArrowRight,
  CheckCircle2,
  Shield,
  Cpu,
  FileText,
  Image,
  Video,
  ChevronRight,
} from 'lucide-react'

const features = [
  {
    icon: Cpu,
    title: 'AI-Powered Detection',
    desc: 'Intelligent watchpoints automatically identify what matters on each page — prices, availability, text, and more.',
  },
  {
    icon: Bell,
    title: 'Real-Time Alerts',
    desc: 'Instant WebSocket notifications the moment a change is detected. No polling delays, no missed updates.',
  },
  {
    icon: Globe,
    title: 'Any URL, Any Format',
    desc: 'Monitor web pages, PDFs, images, videos, and text snippets — everything in one unified dashboard.',
  },
  {
    icon: History,
    title: 'Full Snapshot History',
    desc: 'Every change is recorded with a before/after snapshot so you always have a complete audit trail.',
  },
  {
    icon: Shield,
    title: 'Significance Scoring',
    desc: 'AI rates each change by importance. Filter out noise and focus only on what truly matters.',
  },
  {
    icon: Zap,
    title: 'Flexible Scheduling',
    desc: 'Check as often as every minute or as infrequently as once a week. You set the cadence.',
  },
]

const steps = [
  {
    num: '01',
    title: 'Add a URL',
    desc: 'Paste any web address — product pages, news articles, competitor sites, government portals, research papers.',
  },
  {
    num: '02',
    title: 'AI Extracts Watchpoints',
    desc: 'Our model analyzes the page and identifies the fields worth monitoring: prices, stock status, text blocks, images.',
  },
  {
    num: '03',
    title: 'Get Notified Instantly',
    desc: 'The moment something changes, you receive a real-time notification with a precise diff of what changed.',
  },
]

const contentTypes = [
  { icon: Globe, label: 'Web Pages' },
  { icon: Image, label: 'Images' },
  { icon: Video, label: 'Videos' },
  { icon: FileText, label: 'PDFs' },
  { icon: Eye, label: 'Text Snippets' },
]

export default function Landing() {
  const token = useAuthStore((s) => s.token)
  const [dark, setDark] = useTheme()

  if (token) return <Navigate to="/dashboard" replace />

  return (
    <div className="min-h-screen bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 transition-colors duration-300">

      {/* ─── NAV ─────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 font-bold text-sm">
              K
            </div>
            <span className="font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight">KeepShot</span>
          </div>

          {/* Nav links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-600 dark:text-zinc-400">
            <a href="#features" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">Features</a>
            <a href="#how" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">How It Works</a>
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setDark((d) => !d)}
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-200 dark:border-zinc-800 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all"
              aria-label="Toggle theme"
            >
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <Link
              to="/login"
              className="hidden sm:block text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors px-3 py-2"
            >
              Sign in
            </Link>
            <Link
              to="/register"
              className="flex items-center gap-1.5 rounded-lg bg-zinc-900 dark:bg-white px-4 py-2 text-sm font-semibold text-white dark:text-zinc-900 hover:bg-zinc-700 dark:hover:bg-zinc-100 transition-colors"
            >
              Get started <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </header>

      {/* ─── HERO ────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden px-6 pt-24 pb-32">
        {/* Subtle grid background */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.03] dark:opacity-[0.05]"
          style={{
            backgroundImage:
              'linear-gradient(to right, currentColor 1px, transparent 1px), linear-gradient(to bottom, currentColor 1px, transparent 1px)',
            backgroundSize: '64px 64px',
          }}
        />
        {/* Radial glow */}
        <div className="pointer-events-none absolute inset-0 flex items-start justify-center">
          <div className="mt-12 h-96 w-96 rounded-full bg-zinc-200 dark:bg-zinc-800 opacity-30 blur-3xl" />
        </div>

        <div className="relative mx-auto max-w-4xl text-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 px-4 py-1.5 text-xs font-medium text-zinc-600 dark:text-zinc-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            AI-powered bookmark monitoring
          </div>

          <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold tracking-tight leading-[1.1] text-zinc-900 dark:text-white">
            Monitor what
            <br />
            <span className="text-zinc-400 dark:text-zinc-500">matters most.</span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-zinc-600 dark:text-zinc-400 leading-relaxed">
            KeepShot watches any URL — web pages, PDFs, images, videos — and alerts you the instant something changes. Powered by AI that understands context, not just diffs.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to="/register"
              className="flex items-center gap-2 rounded-xl bg-zinc-900 dark:bg-white px-6 py-3.5 text-sm font-semibold text-white dark:text-zinc-900 hover:bg-zinc-700 dark:hover:bg-zinc-100 transition-colors shadow-lg shadow-zinc-900/10 dark:shadow-white/5"
            >
              Start monitoring free <ArrowRight size={15} />
            </Link>
            <Link
              to="/login"
              className="flex items-center gap-2 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-6 py-3.5 text-sm font-semibold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
            >
              Sign in to your account
            </Link>
          </div>

          {/* Content type pills */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-2">
            {contentTypes.map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-1.5 rounded-full border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/60 px-3 py-1.5 text-xs text-zinc-600 dark:text-zinc-400"
              >
                <Icon size={12} />
                {label}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── STATS BAR ───────────────────────────────────────────────────── */}
      <div className="border-y border-zinc-100 dark:border-zinc-900 bg-zinc-50 dark:bg-zinc-900/40 px-6 py-8">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-8 sm:grid-cols-4 text-center">
          {[
            { value: '5', label: 'Content types' },
            { value: '60s', label: 'Min check interval' },
            { value: 'AI', label: 'Significance scoring' },
            { value: 'WS', label: 'Real-time push' },
          ].map(({ value, label }) => (
            <div key={label}>
              <div className="text-2xl font-bold text-zinc-900 dark:text-white">{value}</div>
              <div className="mt-1 text-xs text-zinc-500 dark:text-zinc-500">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ─── FEATURES ────────────────────────────────────────────────────── */}
      <section id="features" className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mb-16 text-center">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-white">
              Everything you need to stay informed
            </h2>
            <p className="mt-4 text-zinc-600 dark:text-zinc-400 max-w-xl mx-auto">
              Built for professionals who can't afford to miss a change on the pages that matter most.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, desc }) => (
              <div
                key={title}
                className="group rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 p-6 hover:border-zinc-300 dark:hover:border-zinc-700 transition-all"
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 group-hover:bg-zinc-200 dark:group-hover:bg-zinc-700 transition-colors">
                  <Icon size={18} />
                </div>
                <h3 className="mb-2 font-semibold text-zinc-900 dark:text-zinc-100">{title}</h3>
                <p className="text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ────────────────────────────────────────────────── */}
      <section id="how" className="bg-zinc-50 dark:bg-zinc-900/30 border-y border-zinc-100 dark:border-zinc-900 px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <div className="mb-16 text-center">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-white">
              Up and running in seconds
            </h2>
            <p className="mt-4 text-zinc-600 dark:text-zinc-400">
              No configuration required. Just add a URL and let AI handle the rest.
            </p>
          </div>

          <div className="relative grid gap-8 sm:grid-cols-3">
            {/* Connector line */}
            <div className="absolute top-8 left-0 right-0 hidden sm:block">
              <div className="mx-auto h-px w-2/3 bg-gradient-to-r from-transparent via-zinc-300 dark:via-zinc-700 to-transparent" />
            </div>

            {steps.map(({ num, title, desc }) => (
              <div key={num} className="relative text-center">
                <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border-2 border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-xl font-bold text-zinc-400 dark:text-zinc-600">
                  {num}
                </div>
                <h3 className="mb-2 font-semibold text-zinc-900 dark:text-zinc-100">{title}</h3>
                <p className="text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          {/* Checklist */}
          <div className="mt-16 mx-auto max-w-xl rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 p-8">
            <p className="mb-5 text-sm font-semibold text-zinc-700 dark:text-zinc-300 uppercase tracking-widest">
              Included out of the box
            </p>
            <ul className="space-y-3">
              {[
                'Automated watchpoint extraction',
                'AI-rated change significance',
                'Historical snapshot storage',
                'Real-time WebSocket notifications',
                'REST API for custom integrations',
                'Configurable monitoring intervals',
              ].map((item) => (
                <li key={item} className="flex items-center gap-3 text-sm text-zinc-700 dark:text-zinc-300">
                  <CheckCircle2 size={16} className="flex-shrink-0 text-emerald-500" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ─── FINAL CTA ───────────────────────────────────────────────────── */}
      <section className="px-6 py-28">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-zinc-900 dark:bg-white">
            <Bookmark size={22} className="text-white dark:text-zinc-900" />
          </div>
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight text-zinc-900 dark:text-white">
            Never miss a change again.
          </h2>
          <p className="mt-5 text-lg text-zinc-600 dark:text-zinc-400">
            Join and start monitoring the URLs that matter most to you — for free.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to="/register"
              className="flex items-center gap-2 rounded-xl bg-zinc-900 dark:bg-white px-8 py-3.5 text-sm font-semibold text-white dark:text-zinc-900 hover:bg-zinc-700 dark:hover:bg-zinc-100 transition-colors shadow-lg shadow-zinc-900/10 dark:shadow-white/5"
            >
              Create free account <ChevronRight size={15} />
            </Link>
            <Link
              to="/login"
              className="text-sm font-medium text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              Already have an account? Sign in
            </Link>
          </div>
        </div>
      </section>

      {/* ─── FOOTER ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-zinc-100 dark:border-zinc-900 px-6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 font-bold text-xs">
              K
            </div>
            <span className="text-sm font-medium text-zinc-600 dark:text-zinc-500">KeepShot</span>
          </div>
          <p className="text-xs text-zinc-400 dark:text-zinc-600">
            &copy; {new Date().getFullYear()} KeepShot. All rights reserved.
          </p>
          <div className="flex items-center gap-5 text-xs text-zinc-500 dark:text-zinc-500">
            <Link to="/login" className="hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors">Sign in</Link>
            <Link to="/register" className="hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors">Register</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
