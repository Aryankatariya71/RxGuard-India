import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import type { Alert } from '../../api/types'
import { tierMeta } from '../../lib/severity'

interface Props {
  alerts: Alert[]
  onWhy: (a: Alert) => void
}

export function AlertList({ alerts, onWhy }: Props) {
  const critical = alerts.filter((a) => a.tier === 'critical')
  const review = alerts.filter((a) => a.tier === 'review')
  const info = alerts.filter((a) => a.tier === 'info')

  return (
    <div className="print-report space-y-4">
      <TierGroup title="Critical" tier="critical" items={critical} defaultOpen onWhy={onWhy} />
      <TierGroup title="Review" tier="review" items={review} defaultOpen onWhy={onWhy} />
      <TierGroup title="Info" tier="info" items={info} defaultOpen={false} onWhy={onWhy} />
      {alerts.length === 0 && (
        <p className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
          No alerts for resolved lines.
        </p>
      )}
    </div>
  )
}

function TierGroup({
  title,
  tier,
  items,
  defaultOpen,
  onWhy,
}: {
  title: string
  tier: string
  items: Alert[]
  defaultOpen: boolean
  onWhy: (a: Alert) => void
}) {
  const [open, setOpen] = useState(defaultOpen)
  const m = tierMeta(tier)
  const Icon = m.icon
  if (items.length === 0) return null

  return (
    <div className={`rounded-2xl border ${m.border}`}>
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span className={`flex items-center gap-2 text-sm font-bold ${m.className}`}>
          <Icon className="h-4 w-4" aria-hidden />
          {title}
          <span className="rounded-full bg-black/20 px-2 py-0.5 text-xs">{items.length}</span>
        </span>
        <ChevronDown className={`h-4 w-4 transition ${open ? 'rotate-180' : ''}`} aria-hidden />
      </button>
      {open && (
        <ul className="space-y-2 border-t border-[var(--card-border)] p-3">
          {items.map((a) => (
            <li key={a.id} className="glass rounded-2xl p-4">
              <div className="flex items-start gap-3">
                <span className={`mt-0.5 rounded-lg p-1.5 ${m.bg} ${m.className}`}>
                  <Icon className="h-4 w-4" aria-hidden />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-semibold leading-snug">{a.title}</p>
                  <p className="mt-1 text-sm text-[var(--muted)]">{a.reason}</p>
                  <p className="mt-2 text-sm">
                    <span className="font-medium text-teal-300">Action: </span>
                    {a.suggested_action}
                  </p>
                  <button
                    type="button"
                    onClick={() => onWhy(a)}
                    className="mt-3 rounded-xl border border-teal-500/30 bg-teal-500/10 px-3 py-1.5 text-xs font-semibold text-teal-200 transition hover:bg-teal-500/20"
                  >
                    Why?
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
