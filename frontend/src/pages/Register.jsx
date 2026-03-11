import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, ArrowRight, Check, Moon, Sun } from 'lucide-react'
import { authApi } from '../api/client'
import { useAuthStore } from '../store/auth'
import { useTheme } from '../hooks/useTheme'

function PasswordStrength({ password }) {
  const checks = [
    { label: '8+ characters', ok: password.length >= 8 },
    { label: 'Uppercase letter', ok: /[A-Z]/.test(password) },
    { label: 'Number', ok: /\d/.test(password) },
  ]

  if (!password) return null

  return (
    <div className="flex gap-3 flex-wrap">
      {checks.map(({ label, ok }) => (
        <span
          key={label}
          className={`flex items-center gap-1 text-xs transition-colors ${
            ok ? 'text-emerald-500' : 'text-zinc-400 dark:text-zinc-600'
          }`}
        >
          <Check size={11} strokeWidth={ok ? 3 : 1} />
          {label}
        </span>
      ))}
    </div>
  )
}

export default function Register() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()
  const [dark, setDark] = useTheme()

  async function handleSubmit(e) {
    e.preventDefault()
    if (!username.trim() || !password) return

    setError('')
    setLoading(true)
    try {
      const { data } = await authApi.register(username.trim(), password)
      setAuth(data.access_token, data.user_id, username.trim())
      navigate('/dashboard', { replace: true })
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
          ? detail.map((d) => d.msg).join(', ')
          : 'Registration failed'
      )
    } finally {
      setLoading(false)
    }
  }

  const inputCls =
    'h-11 w-full rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-4 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-600 focus:border-zinc-900 dark:focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 dark:focus:ring-zinc-400/10 transition-all'

  return (
    <div className="flex min-h-screen bg-zinc-50 dark:bg-zinc-950 transition-colors duration-300">
      {/* Left decorative panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-zinc-900 border-r border-zinc-800 flex-col justify-between p-12">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-zinc-900 font-bold text-sm">
            K
          </div>
          <span className="font-semibold text-white tracking-tight">KeepShot</span>
        </Link>

        <div className="space-y-6">
          {[
            { title: 'AI-powered watchpoints', desc: 'Automatically identifies what to monitor on every page.' },
            { title: 'Real-time notifications', desc: 'Instant alerts the moment a change is detected.' },
            { title: 'Full history', desc: 'Every change is saved with before/after snapshots.' },
          ].map(({ title, desc }) => (
            <div key={title} className="flex gap-3">
              <div className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-emerald-500" />
              <div>
                <p className="text-sm font-semibold text-white">{title}</p>
                <p className="mt-0.5 text-sm text-zinc-500">{desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-4 text-xs text-zinc-600">
          <span>Free to start</span>
          <span>&middot;</span>
          <span>No credit card</span>
          <span>&middot;</span>
          <span>Ready in seconds</span>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex flex-1 flex-col">
        <div className="flex items-center justify-between px-6 py-5">
          <Link to="/" className="flex items-center gap-2 lg:hidden">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 font-bold text-xs">
              K
            </div>
            <span className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">KeepShot</span>
          </Link>
          <div className="flex lg:w-full lg:justify-end items-center gap-4">
            <button
              onClick={() => setDark((d) => !d)}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-zinc-200 dark:border-zinc-800 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
              aria-label="Toggle theme"
            >
              {dark ? <Sun size={15} /> : <Moon size={15} />}
            </button>
            <span className="text-sm text-zinc-500 dark:text-zinc-400">
              Have an account?{' '}
              <Link to="/login" className="font-semibold text-zinc-900 dark:text-zinc-100 hover:underline">
                Sign in
              </Link>
            </span>
          </div>
        </div>

        <div className="flex flex-1 items-center justify-center px-6 py-12">
          <div className="w-full max-w-sm">
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Create your account</h1>
              <p className="mt-1.5 text-sm text-zinc-500 dark:text-zinc-400">
                Start monitoring everything that matters
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Username</label>
                <input
                  type="text"
                  placeholder="choose_a_username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  autoFocus
                  className={inputCls}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Password</label>
                <div className="relative">
                  <input
                    type={showPw ? 'text' : 'password'}
                    placeholder="Create a strong password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="new-password"
                    className={inputCls + ' pr-11'}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw((v) => !v)}
                    className="absolute inset-y-0 right-0 flex items-center px-3.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 transition-colors"
                    tabIndex={-1}
                  >
                    {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
                <PasswordStrength password={password} />
              </div>

              {error && (
                <p className="rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 px-4 py-2.5 text-sm text-red-600 dark:text-red-400">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl bg-zinc-900 dark:bg-white px-4 py-3 text-sm font-semibold text-white dark:text-zinc-900 hover:bg-zinc-700 dark:hover:bg-zinc-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <span className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />
                ) : (
                  <>Create account <ArrowRight size={15} /></>
                )}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-zinc-500 dark:text-zinc-500">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-zinc-900 dark:text-zinc-100 hover:underline">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
