const presets = {
  url: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  text: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  image: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  pdf: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  video: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  live: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  off: 'bg-zinc-700/50 text-zinc-400 border-zinc-700',
  changed: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  error: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
}

export default function Badge({ label, preset, className = '' }) {
  const style = presets[preset] || 'bg-zinc-700/50 text-zinc-400 border-zinc-700'
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${style} ${className}`}
    >
      {preset === 'live' && (
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
      )}
      {label}
    </span>
  )
}
