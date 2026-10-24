import { Link, NavLink, Outlet } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import { BannerDisclaimer } from '../common/Disclaimer'

const links = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/review/new', label: 'New review' },
  { to: '/medicines', label: 'Catalogue' },
  { to: '/history', label: 'History' },
  { to: '/how-it-works', label: 'How it works' },
  { to: '/settings', label: 'Settings' },
]

export function AppShell() {
  return (
    <div className="min-h-screen">
      <header className="no-print sticky top-0 z-40 border-b border-[var(--color-border)] bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/" className="flex items-center gap-2 font-bold text-[var(--color-ink)]">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--color-primary)] text-white">
              <ShieldCheck className="h-5 w-5" aria-hidden />
            </span>
            <span>
              RxGuard India
              <span className="block text-[11px] font-medium text-[var(--color-muted)]">
                Smarter Prescription Reviews
              </span>
            </span>
          </Link>
          <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-2 text-sm ${
                    isActive
                      ? 'bg-blue-50 font-semibold text-[var(--color-primary)]'
                      : 'text-[var(--color-muted)] hover:text-[var(--color-ink)]'
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
          </nav>
          <Link to="/review/new" className="btn-primary text-xs sm:text-sm">
            Start review
          </Link>
        </div>
        <nav
          className="flex gap-1 overflow-x-auto border-t border-[var(--color-border)] px-4 py-2 md:hidden"
          aria-label="Mobile"
        >
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                `whitespace-nowrap rounded-lg px-2.5 py-1.5 text-xs ${
                  isActive
                    ? 'bg-blue-50 font-semibold text-[var(--color-primary)]'
                    : 'text-[var(--color-muted)]'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <div className="mx-auto max-w-6xl px-4 pt-4">
        <BannerDisclaimer />
      </div>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
      <footer className="no-print border-t border-[var(--color-border)] py-8 text-center text-sm text-[var(--color-muted)]">
        RxGuard India v1.0.0-hm02 · Prototype · Not clinically validated · Demo data labeled DEMO_ONLY
      </footer>
    </div>
  )
}
