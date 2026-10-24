import { Link } from 'react-router-dom'
import { Layers, Search, Shield } from 'lucide-react'
import { BannerDisclaimer } from '../components/common/Disclaimer'

export function Landing() {
  return (
    <div className="-mx-4 -mt-6">
      <section className="border-b border-[var(--color-border)] bg-white px-4 py-16">
        <div className="mx-auto max-w-6xl">
          <p className="text-sm font-semibold text-[var(--color-primary)]">HM-02 · SIH 2026 prototype</p>
          <h1 className="mt-3 max-w-3xl text-4xl font-extrabold tracking-tight sm:text-5xl">
            Know What&apos;s Inside Every Medicine.
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-[var(--color-muted)]">
            Review Indian medicine brands at the ingredient level and identify potential
            prescription concerns with transparent, rule-based safety insights.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/review/new" className="btn-primary">
              Start Prescription Review
            </Link>
            <Link to="/how-it-works" className="btn-secondary">
              Explore How It Works
            </Link>
          </div>
          <div className="mt-8">
            <BannerDisclaimer />
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-4 py-12 sm:grid-cols-3">
        {[
          {
            icon: Search,
            title: 'Brand → ingredients',
            body: 'Resolve catalogue products, including combination medicines, without guessing.',
          },
          {
            icon: Layers,
            title: 'Duplicate detection',
            body: 'Flag the same active ingredient across multiple brands in one review.',
          },
          {
            icon: Shield,
            title: 'Configured rules only',
            body: 'Deterministic interaction and dosage checks with rule versions and DEMO labels.',
          },
        ].map(({ icon: Icon, title, body }) => (
          <div key={title} className="card p-5">
            <Icon className="h-5 w-5 text-[var(--color-primary)]" aria-hidden />
            <h2 className="mt-3 font-bold">{title}</h2>
            <p className="mt-2 text-sm text-[var(--color-muted)]">{body}</p>
          </div>
        ))}
      </section>

      <section className="border-t border-[var(--color-border)] bg-white px-4 py-12">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-2xl font-bold">Three steps</h2>
          <ol className="mt-6 grid gap-4 sm:grid-cols-3">
            {['Create a review & patient context', 'Search and add medicines', 'Run the safety engine & inspect findings'].map(
              (t, i) => (
                <li key={t} className="card p-5">
                  <span className="text-sm font-bold text-[var(--color-primary)]">Step {i + 1}</span>
                  <p className="mt-2 font-medium">{t}</p>
                </li>
              ),
            )}
          </ol>
          <p className="mt-8 text-sm text-[var(--color-muted)]">
            Demo catalogue uses clearly fictional DEMO-Brand / Ingredient-Demo names. Missing
            alerts never mean a prescription is safe.
          </p>
        </div>
      </section>
    </div>
  )
}
