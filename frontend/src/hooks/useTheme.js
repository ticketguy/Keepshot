import { useState, useEffect } from 'react'

export function useTheme() {
  const [dark, setDark] = useState(() => {
    const stored = localStorage.getItem('ks_theme')
    if (stored) return stored === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    const el = document.documentElement
    if (dark) {
      el.classList.add('dark')
    } else {
      el.classList.remove('dark')
    }
    localStorage.setItem('ks_theme', dark ? 'dark' : 'light')
  }, [dark])

  return [dark, setDark]
}
