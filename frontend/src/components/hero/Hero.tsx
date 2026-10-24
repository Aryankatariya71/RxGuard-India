import { useEffect, useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { ArrowDown, Database, Lock, Sparkles } from 'lucide-react'
import { FloatingVisual } from './FloatingVisual'

type Stats = {
  total_products: number
  synthetic_products: number
  source_backed_products: number
  india_catalogue_products: number
  rxnorm_products: number
}

export function Hero() {
  const reduce = useReducedMotion()
  const [stats, setStats] = useState<Stats | null>(null)

  useEffect(() => {
    fetch('/api/catalogue/stats', { signal: AbortSignal.timeout(5000) })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setStats(d))
      .catch(() => setStats(null))
  }, [])

  const chips = [
    {
      icon: Database,
      label: stats
        ? `${stats.total_products.toLocaleString()} products in local DB`
        : 'Catalogue stats loading…',
    },
    {
      icon: Lock,
      label: 'Explainable rules, no black box',
    },
    {
      icon: Sparkles,
      label: stats
        ? `${stats.source_backed_products} source-backed · ${stats.synthetic_products} demo`
        : 'Demo rules labeled DEMO_ONLY',
    },
  ]

  return (
    <section id="top" className="relative overflow-hidden">
      <div className="aurora absolute inset-0 -z-10" />
      <div className="grid-noise absolute inset-0 -z-10 opacity-70" />

      <div className="mx-auto grid max-w-7xl items-center gap-10 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:py-24">
        <div>
          <motion.p
            initial={reduce ? false : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 inline-flex items-center gap-2 rounded-full border border-teal-500/25 bg-teal-500/10 px-3 py-1 text-xs font-medium text-teal-300"
          >
            <ShieldDot /> Prescription Safety Checker
          </motion.p>

          <motion.h1
            initial={reduce ? false : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="text-4xl font-extrabold leading-[1.08] tracking-tight sm:text-5xl lg:text-[3.4rem]"
          >
            Catch the hidden risks in{' '}
            <span className="text-gradient">Indian prescriptions</span>
          </motion.h1>

          <motion.p
            initial={reduce ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12 }}
            className="mt-5 max-w-xl text-lg text-[var(--muted)]"
          >
            Every brand. Every ingredient. Every risk. Explained.
          </motion.p>

          <motion.div
            initial={reduce ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.18 }}
            className="mt-8 flex flex-wrap gap-2"
          >
            {chips.map(({ icon: Icon, label }, idx) => (
              <motion.div
                key={label}
                initial={reduce ? false : { opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.22 + idx * 0.06 }}
                className="glass flex items-center gap-2 rounded-2xl px-3.5 py-2 text-sm"
              >
                <Icon className="h-4 w-4 text-teal-400" aria-hidden />
                <span>{label}</span>
              </motion.div>
            ))}
          </motion.div>

          <motion.a
            href="#checker"
            initial={reduce ? false : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="btn-glow mt-10 inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-teal-500 to-indigo-500 px-6 py-3.5 text-sm font-semibold text-white transition hover:brightness-110"
          >
            Try the checker
            <ArrowDown className="h-4 w-4" aria-hidden />
          </motion.a>
        </div>

        <motion.div
          initial={reduce ? false : { opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <FloatingVisual />
        </motion.div>
      </div>
    </section>
  )
}

function ShieldDot() {
  return <span className="inline-block h-1.5 w-1.5 rounded-full bg-teal-400" aria-hidden />
}
