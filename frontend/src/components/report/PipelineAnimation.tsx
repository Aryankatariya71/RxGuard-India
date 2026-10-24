import { motion, useReducedMotion } from 'framer-motion'

const STEPS = [
  'Parse',
  'Match brands',
  'Split ingredients',
  'Sum daily dose',
  'Check rules',
]

interface Props {
  active: boolean
}

export function PipelineAnimation({ active }: Props) {
  const reduce = useReducedMotion()
  if (!active) return null

  return (
    <div className="glass rounded-2xl p-4" role="status" aria-live="polite" aria-label="Analysis pipeline running">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
        Running checks
      </p>
      <div className="relative flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        {!reduce && (
          <motion.div
            className="absolute left-0 right-0 top-1/2 hidden h-0.5 -translate-y-1/2 bg-gradient-to-r from-teal-500/20 via-indigo-500/40 to-teal-500/20 sm:block"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 2.2, ease: 'easeInOut' }}
            style={{ transformOrigin: 'left' }}
          />
        )}
        {STEPS.map((step, i) => (
          <motion.div
            key={step}
            initial={reduce ? false : { opacity: 0.3, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.35, duration: 0.35 }}
            className="relative z-10 flex items-center gap-2 rounded-xl border border-teal-500/25 bg-[var(--bg)] px-3 py-2 text-xs font-medium"
          >
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-teal-500/20 text-[10px] font-bold text-teal-300">
              {i + 1}
            </span>
            {step}
          </motion.div>
        ))}
      </div>
    </div>
  )
}
