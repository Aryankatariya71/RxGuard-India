import { motion, useReducedMotion } from 'framer-motion'

export function AlertFatigue() {
  const reduce = useReducedMotion()
  return (
    <section className="no-print border-t border-[#DCE8E4] bg-white py-14 sm:py-16">
      <div className="rx-container">
        <h2 className="text-3xl font-bold tracking-tight text-[#123C38] sm:text-4xl">
          Less noise. More signal.
        </h2>
        <p className="rx-prose mt-3 text-[#64748B]">
          Tiering, merging, and de-duplication collapse naive alert spam into actionable cards.
        </p>
        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <motion.div
            initial={reduce ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="rx-card border-[#FECACA] bg-[#FEF2F2]/50 p-6"
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-[#B91C1C]">
              Naive checker
            </p>
            <p className="mt-2 text-4xl font-bold text-[#B91C1C]">14 alerts</p>
            <ul className="mt-4 space-y-1.5 text-sm text-[#334155]">
              <li>Duplicate ×3 + dose ×3 + interactions ×8</li>
              <li>Same ingredient repeated in separate cards</li>
              <li>No severity ordering</li>
            </ul>
          </motion.div>
          <motion.div
            initial={reduce ? false : { opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="rx-card border-[#BBF7D0] bg-[#F0FDF4]/60 p-6"
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-[#15803D]">RxGuard</p>
            <p className="mt-2 text-4xl font-bold text-[#15803D]">
              2 critical <span className="text-lg font-semibold text-[#334155]">+ 1 review</span>
            </p>
            <ul className="mt-4 space-y-1.5 text-sm text-[#334155]">
              <li>Duplicate + dose merged into one card</li>
              <li>Identical interaction pairs collapsed</li>
              <li>Critical sorted first, info collapsed</li>
            </ul>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
