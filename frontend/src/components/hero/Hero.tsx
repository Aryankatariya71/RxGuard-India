import { useEffect, useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { ClipboardList, Database, Lock, ShieldCheck } from 'lucide-react'
import { FloatingVisual } from './FloatingVisual'

type Stats = {
  total_products: number
  synthetic_products: number
  source_backed_products: number
}

export function Hero() {
  const reduce = useReducedMotion()
  const [stats, setStats] = useState<Stats | null>(null)
  const [imgOk, setImgOk] = useState(true)

  useEffect(() => {
    fetch('/api/catalogue/stats', { signal: AbortSignal.timeout(5000) })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setStats(d))
      .catch(() => setStats(null))
  }, [])

  return (
    <section id="top" className="relative overflow-hidden bg-[#F1F7F5]">
      <div className="rx-container grid items-center gap-10 py-12 lg:grid-cols-2 lg:gap-12 lg:py-16 xl:gap-16">
        <div>
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
            className="rx-prose mt-5 text-base leading-relaxed text-[#334155] sm:text-lg"
          >
            Understand potential medicine risks, duplicate ingredients, and possible interactions
            with clear, explainable prescription safety checks.
          </motion.p>

          <motion.div
            initial={reduce ? false : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.16 }}
            className="mt-8 flex flex-wrap gap-3"
          >
            <a
              href="#checker"
              className="btn-primary inline-flex items-center gap-2 px-6 py-3.5 text-sm text-white"
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
              <Lock className="h-4 w-4 shrink-0 text-[#087F6E]" strokeWidth={2} aria-hidden />
              Explainable rules — not a black box
            </li>
            <li className="inline-flex items-center gap-2 text-sm text-[#64748B]">
              <Database className="h-4 w-4 shrink-0 text-[#087F6E]" strokeWidth={2} aria-hidden />
              {stats
                ? `${stats.total_products.toLocaleString()} products in local catalogue`
                : 'Local medicine catalogue'}
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
          className="relative"
        >
          {imgOk ? (
            <div className="relative overflow-hidden rounded-2xl border border-[#DCE8E4] bg-[#DDF5EC] shadow-[0_8px_30px_rgba(7,83,77,0.08)]">
              <img
                src="/images/hero-healthcare.jpg"
                alt="Healthcare professional reviewing clinical information on a computer"
                width={1600}
                height={1067}
                className="aspect-[4/3] w-full object-cover"
                onError={() => setImgOk(false)}
                fetchPriority="high"
              />
              <div
                className="pointer-events-none absolute inset-0 bg-gradient-to-tr from-[#07534D]/25 via-transparent to-[#DDF5EC]/20"
                aria-hidden
              />
              <div className="absolute bottom-4 left-4 right-4 sm:left-auto sm:right-4 sm:w-64">
                <div className="rounded-xl border border-white/70 bg-white/95 p-3 shadow-sm backdrop-blur-sm">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-[#087F6E]">
                    Brand → ingredients
                  </p>
                  <p className="mt-1 font-mono text-sm font-semibold text-[#123C38]">Combiflam</p>
                  <p className="mt-0.5 font-mono text-xs text-[#64748B]">
                    Ibuprofen · Paracetamol
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <FloatingVisual />
          )}
        </motion.div>
      </div>
    </section>
  )
}
