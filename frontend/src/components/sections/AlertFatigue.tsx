import { motion, useReducedMotion } from 'framer-motion'

export function AlertFatigue() {
  const reduce = useReducedMotion()
  return (
    <section className="no-print mx-auto max-w-7xl px-4 py-16 sm:px-6">
      <h2 className="text-3xl font-extrabold tracking-tight">Less noise. More signal.</h2>
      <p className="mt-3 max-w-2xl text-[var(--muted)]">
        Tiering, merging, and de-duplication collapse naive alert spam into actionable cards.
      </p>
      <div className="mt-10 grid gap-6 lg:grid-cols-2">
        <motion.div
          initial={reduce ? false : { opacity: 0, x: -12 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          className="glass rounded-[1.5rem] p-6"
        >
          <p className="text-xs font-bold uppercase tracking-wider text-rose-300">Naive checker</p>
          <p className="mt-2 text-4xl font-extrabold text-rose-400">14 alerts</p>
          <ul className="mt-4 space-y-1 text-sm text-[var(--muted)]">
            <li>Duplicate ×3 + dose ×3 + interactions ×8</li>
            <li>Same ingredient repeated in separate cards</li>
            <li>No severity ordering</li>
          </ul>
        </motion.div>
        <motion.div
          initial={reduce ? false : { opacity: 0, x: 12 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          className="glass rounded-[1.5rem] border-teal-500/30 p-6"
        >
          <p className="text-xs font-bold uppercase tracking-wider text-teal-300">RxGuard</p>
          <p className="mt-2 text-4xl font-extrabold text-teal-300">
            2 critical <span className="text-lg text-[var(--muted)]">+ 1 review</span>
          </p>
          <ul className="mt-4 space-y-1 text-sm text-[var(--muted)]">
            <li>Duplicate + dose merged into one card</li>
            <li>Identical interaction pairs collapsed</li>
            <li>Critical sorted first, info collapsed</li>
          </ul>
        </motion.div>
      </div>
    </section>
  )
}
