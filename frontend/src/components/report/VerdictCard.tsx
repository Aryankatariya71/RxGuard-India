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

  let headline = 'No matching critical rule in this prototype dataset'
  let Icon = ShieldCheck
  let tone = 'text-[#1D4ED8]'
  let cardTint = 'border-[#BFDBFE] bg-[#EFF6FF]/40'

  if (verdict === 'action_needed' || critical > 0) {
    headline = `Review recommended: ${critical} critical finding${critical === 1 ? '' : 's'}`
    Icon = ShieldAlert
    tone = 'text-[#B91C1C]'
    cardTint = 'border-[#FECACA] bg-[#FEF2F2]/50'
  } else if (verdict === 'review' || review > 0) {
    headline = `Potential findings: ${review} item${review === 1 ? '' : 's'} for review`
    Icon = Shield
    tone = 'text-[#B45309]'
    cardTint = 'border-[#FED7AA] bg-[#FFF7ED]/50'
  }

  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`print-report relative overflow-hidden rounded-2xl border p-6 ${cardTint}`}
    >
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
        <div
          className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-white ${tone}`}
        >
          <Icon className="h-8 w-8" aria-hidden />
        </div>
        <div className="flex-1">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--muted)]">
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
              className={`rounded-2xl border bg-white px-3 py-3 text-center ${m.border}`}
            >
              <div
                className={`mx-auto mb-1 flex items-center justify-center gap-1 text-[10px] font-semibold sm:text-xs ${m.className}`}
              >
                <I className="h-3.5 w-3.5" aria-hidden />
                <span className="hidden sm:inline">{m.label}</span>
                <span className="sm:hidden">{tier === 'critical' ? 'Urgent' : tier === 'review' ? 'Check' : 'Info'}</span>
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
