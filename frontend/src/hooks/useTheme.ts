import { useEffect, useState } from 'react'

/** Product ships as a light Medcare-style dashboard. Toggle kept for compatibility. */
type Theme = 'dark' | 'light'

export function useTheme() {
  const [theme, setTheme] = useState<Theme>('light')

  useEffect(() => {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('rxguard-theme', 'light')
  }, [theme])

  const toggle = () => setTheme('light')

  return { theme, toggle, setTheme }
}
