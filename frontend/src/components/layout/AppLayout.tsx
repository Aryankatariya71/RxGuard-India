import type { ReactNode } from 'react'
import { Footer } from './Footer'
import { TopNav } from './TopNav'

interface Props {
  children: ReactNode
  /** Kept for call-site compatibility; page content owns its headings. */
  title?: string
  subtitle?: string
}

export function AppLayout({ children }: Props) {
  return (
    <div className="flex min-h-screen flex-col bg-[var(--bg)] text-[var(--fg)]">
      <TopNav />
      <main className="w-full flex-1">{children}</main>
      <Footer />
    </div>
  )
}
