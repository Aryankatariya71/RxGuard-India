import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { useEffect, useState } from 'react'

const FRAMES = [
  { brand: 'Combiflam', parts: ['Ibuprofen 400 mg', 'Paracetamol 325 mg'] },
  { brand: 'Augmentin 625', parts: ['Amoxicillin 500 mg', 'Clavulanic acid 125 mg'] },
  { brand: 'Dolo 650', parts: ['Paracetamol 650 mg'] },
]

export function FloatingVisual() {
  const reduce = useReducedMotion()
  const [i, setI] = useState(0)

  useEffect(() => {
    if (reduce) return
    const t = setInterval(() => setI((x) => (x + 1) % FRAMES.length), 3200)
    return () => clearInterval(t)
  }, [reduce])

  const frame = FRAMES[i]

  return (
    <div className="relative mx-auto h-[280px] w-full max-w-md sm:h-[320px]" aria-hidden>
      <div className="rx-card absolute inset-4 flex flex-col items-center justify-center bg-white p-6">
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
          Brand → ingredients
        </p>
        <AnimatePresence mode="wait">
          <motion.div
            key={frame.brand}
            initial={reduce ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduce ? undefined : { opacity: 0, y: -8 }}
            transition={{ duration: 0.35 }}
            className="flex w-full flex-col items-center gap-4"
          >
            <div className="rounded-xl border border-[#DCE8E4] bg-[#F0FDF4] px-5 py-2.5 font-mono text-lg font-semibold text-[#123C38]">
              {frame.brand}
            </div>
            <div className="h-8 w-px bg-[#0D9B78]/60" />
            <div className="flex flex-wrap justify-center gap-2">
              {frame.parts.map((p) => (
                <span
                  key={p}
                  className="rounded-xl border border-[#E2EBE8] bg-[#F8FBFA] px-3 py-1.5 font-mono text-xs text-[var(--body)]"
                >
                  {p}
                </span>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}
