import { Navbar } from './components/layout/Navbar'
import { Hero } from './components/hero/Hero'
import { useTheme } from './hooks/useTheme'

export default function App() {
  const { theme, toggle } = useTheme()

  return (
    <div className="min-h-screen">
      <Navbar theme={theme} onToggleTheme={toggle} />
      <main>
        <Hero />
        {/* Stages 2–5 mount checker + remaining sections here */}
        <section id="checker" className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
          <div className="glass rounded-[1.5rem] p-8 text-center text-[var(--muted)]">
            Checker loading in next stage…
          </div>
        </section>
      </main>
    </div>
  )
}
