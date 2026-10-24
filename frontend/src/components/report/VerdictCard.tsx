import { motion, useReducedMotion } from 'framer-motion'
import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react'
import type { AnalyzeResponse } from '../../api/types'
import { AnimatedCounter } from './AnimatedCounter'
import { tierMeta } from '../../lib/severity'

interface Props {
  report: AnalyzeResponse
}

export function VerdictCard({ report }: Props) {
  const reduce = useReducedMotion()
  const { counts, verdict } = report
  const critical = counts?.critical ?? 0
  const review = counts?.review ?? 0
  const info = counts?.info ?? 0

  // Never claim "safe" / "no issues" — cautious labels only
  let headline = 'No matching critical rule in this prototype dataset'
  let Icon = ShieldCheck
  let tone = 'text-sky-300'
  let pulse = false

  if (verdict === 'action_needed' || critical > 0) {
    headline = `Review recommended: ${critical} critical finding${critical === 1 ? '' : 's'}`
    Icon = ShieldAlert
    tone = 'text-rose-400'
    pulse = !reduce
  } else if (verdict === 'review' || review > 0) {
    headline = `Potential findings: ${review} item${review === 1 ? '' : 's'} for review`
    Icon = Shield
    tone = 'text-amber-400'
  }

  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass print-report relative overflow-hidden rounded-[1.5rem] p-6 ${
        critical > 0 ? 'border-rose-500/40' : review > 0 ? 'border-amber-500/30' : 'border-emerald-500/30'
      }`}
    >
      {pulse && (
        <motion.div
          className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-rose-500/20 blur-3xl"
          animate={{ opacity: [0.35, 0.7, 0.35] }}
          transition={{ duration: 2.2, repeat: Infinity }}
        />
      )}
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
        <div className={`flex h-16 w-16 items-center justify-center rounded-2xl bg-black/20 ${tone}`}>
          <Icon className={`h-9 w-9 ${pulse ? 'animate-pulse' : ''}`} aria-hidden />
        </div>
        <div className="flex-1">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">
            Verdict
          </p>
          <h3 className={`mt-1 text-xl font-extrabold tracking-tight sm:text-2xl ${tone}`}>
            {headline}
          </h3>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-3 gap-2">
        {(
          [
            ['critical', critical],
            ['review', review],
            ['info', info],
          ] as const
        ).map(([tier, n]) => {
          const m = tierMeta(tier)
          const I = m.icon
          return (
            <div
              key={tier}
              className={`rounded-2xl border ${m.border} ${m.bg} px-3 py-3 text-center`}
            >
              <div className={`mx-auto mb-1 flex items-center justify-center gap-1 text-xs font-medium ${m.className}`}>
                <I className="h-3.5 w-3.5" aria-hidden />
                {m.label}
              </div>
              <p className={`text-2xl font-bold ${m.className}`}>
                <AnimatedCounter value={n} />
              </p>
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}
