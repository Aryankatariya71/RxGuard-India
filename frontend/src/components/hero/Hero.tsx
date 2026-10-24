import { useEffect, useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { BookOpen, ClipboardList, Database, Lock, ShieldCheck } from 'lucide-react'
import { FloatingVisual } from './FloatingVisual'

type Stats = {
  total_products: number
  synthetic_products: number
  source_backed_products: number
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

  return (
    <section id="top" className="relative overflow-hidden bg-[#F1F7F5]">
      <div className="rx-container grid items-center gap-10 py-12 lg:grid-cols-[minmax(0,0.44fr)_minmax(0,0.56fr)] lg:gap-8 lg:py-16 xl:gap-10">
        <div className="min-w-0">
          <motion.p
            initial={reduce ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#DCE8E4] bg-white px-3 py-1.5 text-xs font-medium text-[#123C38]"
          >
            <ShieldCheck className="h-3.5 w-3.5 text-[#0D9B78]" strokeWidth={2} aria-hidden />
            Prescription safety for India
          </motion.p>

          <motion.h1
            initial={reduce ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="max-w-xl text-4xl font-bold leading-[1.12] tracking-tight text-[#123C38] sm:text-5xl lg:text-[3.25rem]"
          >
            Safer prescriptions.
            <br />
            <span className="text-[#0D9B78]">Better decisions.</span>
          </motion.h1>

          <motion.p
            initial={reduce ? false : { opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mt-5 max-w-[36rem] text-base leading-relaxed text-[#334155] sm:text-lg"
          >
            Understand potential medicine risks, duplicate ingredients, and possible interactions
            through clear, explainable prescription safety checks.
          </motion.p>

          <motion.div
            initial={reduce ? false : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.16 }}
            className="mt-8 flex flex-wrap gap-3"
          >
            <a
              href="#checker"
              className="btn-primary inline-flex items-center gap-2 px-6 py-3.5 text-sm text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#0D9B78]"
            >
              <ClipboardList className="h-4 w-4" strokeWidth={2} aria-hidden />
              Check a prescription
            </a>
            <a
              href="#how-it-works"
              className="btn-secondary inline-flex items-center px-6 py-3.5 text-sm"
            >
              How it works
            </a>
          </motion.div>

          <motion.ul
            initial={reduce ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.22 }}
            className="mt-8 flex flex-col gap-2.5 sm:flex-row sm:flex-wrap"
          >
            <li className="inline-flex items-center gap-2 text-sm text-[#64748B]">
              <Lock className="h-4 w-4 shrink-0 text-[#0D9B78]" strokeWidth={2} aria-hidden />
              Explainable safety checks
            </li>
            <li className="inline-flex items-center gap-2 text-sm text-[#64748B]">
              <Database className="h-4 w-4 shrink-0 text-[#0D9B78]" strokeWidth={2} aria-hidden />
              {stats
                ? `${stats.total_products.toLocaleString()} products in local catalogue`
                : 'Available medicine catalogue'}
            </li>
            <li className="inline-flex items-center gap-2 text-sm text-[#64748B]">
              <BookOpen className="h-4 w-4 shrink-0 text-[#0D9B78]" strokeWidth={2} aria-hidden />
              Source-backed findings where available
            </li>
          </motion.ul>

          <p className="mt-6 max-w-lg text-xs leading-relaxed text-[#82918F]">
            Decision support only. Does not replace a clinician or pharmacist.
          </p>
        </div>

        <motion.div
          initial={reduce ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12, duration: 0.45 }}
          className="relative min-w-0 w-full"
        >
          <FloatingVisual />
        </motion.div>
      </div>
    </section>
  )
}
