import { Link, NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Moon, ShieldCheck, Sun } from 'lucide-react'

interface NavbarProps {
  theme: 'dark' | 'light'
  onToggleTheme: () => void
}

function navCls({ isActive }: { isActive: boolean }) {
  return `hidden rounded-lg px-3 py-2 text-sm transition sm:inline ${
    isActive
      ? 'font-semibold text-[var(--fg)]'
      : 'text-[var(--muted)] hover:text-[var(--fg)]'
  }`
}

export function Navbar({ theme, onToggleTheme }: NavbarProps) {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.45 }}
      className="no-print sticky top-0 z-50 border-b border-[var(--card-border)] bg-[color-mix(in_srgb,var(--bg)_75%,transparent)] backdrop-blur-xl"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link to="/" className="group flex items-center gap-2.5" aria-label="RxGuard India home">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500 to-indigo-500 shadow-lg shadow-teal-500/20">
            <ShieldCheck className="h-5 w-5 text-white" aria-hidden />
          </span>
          <span>
            <span className="block text-sm font-bold tracking-tight sm:text-base">RxGuard India</span>
            <span className="hidden text-[11px] text-[var(--muted)] sm:block">
              Every brand. Every ingredient. Every risk.
            </span>
          </span>
        </Link>

        <nav className="flex flex-wrap items-center justify-end gap-1 sm:gap-2" aria-label="Primary">
          <a
            href="/#how-it-works"
            className="hidden rounded-lg px-3 py-2 text-sm text-[var(--muted)] transition hover:text-[var(--fg)] sm:inline"
          >
            How it works
          </a>
          <a
            href="/#checker"
            className="hidden rounded-lg px-3 py-2 text-sm text-[var(--muted)] transition hover:text-[var(--fg)] md:inline"
          >
            Demo
          </a>
          <NavLink to="/ingredients" className={navCls}>
            Ingredients
          </NavLink>
          <span className="hidden items-center rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[11px] font-medium text-amber-600 dark:text-amber-300 lg:inline-flex">
            Decision support only
          </span>
          <button
            type="button"
            onClick={onToggleTheme}
            className="glass glass-hover ml-1 flex h-10 w-10 items-center justify-center rounded-xl"
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </nav>
      </div>
    </motion.header>
  )
}
