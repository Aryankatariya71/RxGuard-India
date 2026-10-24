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
      {!reduce && (
        <>
          <motion.div
            className="absolute left-[8%] top-[18%] h-16 w-16 rounded-full bg-teal-500/20 blur-xl"
            animate={{ y: [0, -18, 0], x: [0, 10, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            className="absolute right-[10%] top-[30%] h-20 w-20 rounded-full bg-indigo-500/25 blur-xl"
            animate={{ y: [0, 22, 0], x: [0, -12, 0] }}
            transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            className="absolute bottom-[12%] left-[30%] h-14 w-14 rounded-full bg-fuchsia-500/20 blur-xl"
            animate={{ y: [0, -12, 0] }}
            transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
          />
        </>
      )}

      <div className="glass absolute inset-4 flex flex-col items-center justify-center rounded-[1.5rem] p-6">
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">
          Brand → ingredients
        </p>
        <AnimatePresence mode="wait">
          <motion.div
            key={frame.brand}
            initial={reduce ? false : { opacity: 0, y: 12, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduce ? undefined : { opacity: 0, y: -10, scale: 0.96 }}
            transition={{ duration: 0.45 }}
            className="flex w-full flex-col items-center gap-4"
          >
            <div className="rounded-2xl border border-teal-500/30 bg-teal-500/10 px-5 py-2.5 font-mono text-lg font-semibold text-teal-300">
              {frame.brand}
            </div>
            <div className="h-8 w-px bg-gradient-to-b from-teal-400 to-indigo-400" />
            <div className="flex flex-wrap justify-center gap-2">
              {frame.parts.map((p) => (
                <span
                  key={p}
                  className="rounded-xl border border-indigo-400/25 bg-indigo-500/10 px-3 py-1.5 font-mono text-xs text-indigo-200"
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
