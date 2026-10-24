import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import {
  BookOpen,
  ClipboardList,
  FlaskConical,
  Home,
  Info,
  Menu,
  ShieldCheck,
  Activity,
  X,
} from 'lucide-react'

const CHECKER_HREF = '/#checker'
const HOW_HREF = '/#how-it-works'

export function TopNav() {
  const [open, setOpen] = useState(false)
  const close = () => setOpen(false)

  return (
    <header className="no-print sticky top-0 z-50 border-b border-[#0A6B63] bg-[#07534D] shadow-[0_1px_2px_rgba(7,83,77,0.2)]">
      <div className="rx-container flex h-16 items-center gap-4">
        <Link to="/" className="flex min-w-0 shrink-0 items-center gap-2.5" onClick={close}>
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#0D9B78]">
            <ShieldCheck className="h-5 w-5 text-white" strokeWidth={2} aria-hidden />
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-semibold tracking-tight text-white sm:text-[15px]">
              RxGuard India
            </span>
            <span className="hidden text-[11px] text-[#D1FAE5] sm:block">
              Prescription safety
            </span>
          </span>
        </Link>

        <nav
          className="ml-auto hidden items-center gap-0.5 lg:flex"
          aria-label="Primary"
        >
          <NavLink to="/" end className={({ isActive }) => topLinkCls(isActive)}>
            Home
          </NavLink>
          <a href={HOW_HREF} className={topLinkCls(false)}>
            How it works
          </a>
          <a href={CHECKER_HREF} className={topLinkCls(false)}>
            Check prescription
          </a>
          <NavLink to="/ingredients" className={({ isActive }) => topLinkCls(isActive)}>
            Medicines
          </NavLink>
          <NavLink to="/stress-test" className={({ isActive }) => topLinkCls(isActive)}>
            Stress test
          </NavLink>
          <NavLink to="/methodology" className={({ isActive }) => topLinkCls(isActive)}>
            Methodology
          </NavLink>
          <NavLink to="/about" className={({ isActive }) => topLinkCls(isActive)}>
            About
          </NavLink>
          <a
            href={CHECKER_HREF}
            className="ml-3 inline-flex items-center gap-2 rounded-[10px] bg-[#0D9B78] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#087F65] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            <ClipboardList className="h-4 w-4 text-white" strokeWidth={2} aria-hidden />
            Get started
          </a>
        </nav>

        <button
          type="button"
          className="ml-auto inline-flex h-10 w-10 items-center justify-center rounded-[10px] text-[#D1FAE5] hover:bg-white/10 hover:text-white lg:hidden"
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <div className="border-t border-white/10 bg-[#07534D] lg:hidden">
          <nav className="rx-container flex flex-col gap-1 py-3" aria-label="Mobile">
            <NavLink to="/" end onClick={close} className={({ isActive }) => mobileLinkCls(isActive)}>
              <Home className="h-4 w-4 text-[#D1FAE5]" aria-hidden />
              Home
            </NavLink>
            <a href={HOW_HREF} onClick={close} className={mobileLinkCls(false)}>
              <Activity className="h-4 w-4 text-[#D1FAE5]" aria-hidden />
              How it works
            </a>
            <a href={CHECKER_HREF} onClick={close} className={mobileLinkCls(false)}>
              <ClipboardList className="h-4 w-4 text-[#D1FAE5]" aria-hidden />
              Check prescription
            </a>
            <NavLink
              to="/ingredients"
              onClick={close}
              className={({ isActive }) => mobileLinkCls(isActive)}
            >
              <FlaskConical className="h-4 w-4 text-[#D1FAE5]" aria-hidden />
              Medicines
            </NavLink>
            <NavLink
              to="/stress-test"
              onClick={close}
              className={({ isActive }) => mobileLinkCls(isActive)}
            >
              <Activity className="h-4 w-4 text-[#D1FAE5]" aria-hidden />
              Stress test
            </NavLink>
            <NavLink
              to="/methodology"
              onClick={close}
              className={({ isActive }) => mobileLinkCls(isActive)}
            >
              <BookOpen className="h-4 w-4 text-[#D1FAE5]" aria-hidden />
              Methodology
            </NavLink>
            <NavLink to="/about" onClick={close} className={({ isActive }) => mobileLinkCls(isActive)}>
              <Info className="h-4 w-4 text-[#D1FAE5]" aria-hidden />
              About
            </NavLink>
            <a
              href={CHECKER_HREF}
              onClick={close}
              className="mt-2 inline-flex items-center justify-center gap-2 rounded-[10px] bg-[#0D9B78] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#087F65]"
            >
              Get started
            </a>
          </nav>
        </div>
      )}
    </header>
  )
}

function topLinkCls(active: boolean) {
  return `rounded-lg px-3 py-2 text-sm font-medium transition ${
    active
      ? 'bg-[#0A6B63] text-white shadow-[inset_0_-2px_0_0_#0D9B78]'
      : 'text-[#F0FDFA] hover:bg-white/10 hover:text-white'
  }`
}

function mobileLinkCls(active: boolean) {
  return `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium ${
    active ? 'bg-[#0A6B63] text-white' : 'text-[#F0FDFA] hover:bg-white/10 hover:text-white'
  }`
}
