import { motion, useReducedMotion } from 'framer-motion'
import { FileSearch, GitBranch, Pill, Scale, Shield } from 'lucide-react'

const STEPS = [
  { icon: FileSearch, title: 'Parse', body: 'Read free-text Rx lines into structured fields.' },
  { icon: Pill, title: 'Match brands', body: 'Fuzzy-resolve Indian brand names against the catalog.' },
  { icon: GitBranch, title: 'Split ingredients', body: 'Expand combination products into APIs + strengths.' },
  { icon: Scale, title: 'Sum daily dose', body: 'Aggregate mg/day per ingredient across brands.' },
  { icon: Shield, title: 'Check rules', body: 'Duplicate, dose, and interaction rules with cited sources.' },
]

export function HowItWorks() {
  const reduce = useReducedMotion()
  return (
    <section id="how-it-works" className="no-print mx-auto max-w-7xl px-4 py-20 sm:px-6">
      <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl">How it works</h2>
      <p className="mt-3 max-w-2xl text-[var(--muted)]">
        Not a black box: a deterministic rules engine. Every alert shows its rule.
      </p>
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {STEPS.map((s, i) => {
          const Icon = s.icon
          return (
            <motion.div
              key={s.title}
              initial={reduce ? false : { opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ delay: i * 0.06 }}
              className="glass glass-hover rounded-2xl p-5"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500/15 text-teal-300">
                <Icon className="h-5 w-5" aria-hidden />
              </span>
              <p className="mt-4 text-xs font-bold uppercase tracking-wider text-teal-300/80">
                Step {i + 1}
              </p>
              <h3 className="mt-1 font-bold">{s.title}</h3>
              <p className="mt-2 text-sm text-[var(--muted)]">{s.body}</p>
            </motion.div>
          )
        })}
      </div>
      <div className="glass mt-8 rounded-2xl border-teal-500/20 p-5 text-sm">
        <strong className="text-teal-300">Explainable by design.</strong>{' '}
        <span className="text-[var(--muted)]">
          Curated pairs override DDInter; class rules fill gaps; max-dose limits are DRAFT until a
          pharmacist verifies them.
        </span>
      </div>
    </section>
  )
}
