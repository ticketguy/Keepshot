export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  className = '',
  ...props
}) {
  const base =
    'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-zinc-950 disabled:opacity-50 disabled:cursor-not-allowed'

  const variants = {
    primary:
      'bg-indigo-500 hover:bg-indigo-400 text-white focus:ring-indigo-500',
    ghost:
      'bg-transparent hover:bg-zinc-800 text-zinc-300 hover:text-zinc-100 focus:ring-zinc-600',
    danger:
      'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 focus:ring-rose-500',
    outline:
      'bg-transparent border border-zinc-700 hover:border-zinc-500 text-zinc-300 hover:text-zinc-100 focus:ring-zinc-600',
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm h-8',
    md: 'px-4 py-2 text-sm h-9',
    lg: 'px-5 py-2.5 text-base h-11',
  }

  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading && (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      )}
      {children}
    </button>
  )
}
