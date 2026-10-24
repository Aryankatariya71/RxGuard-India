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
      <TierGroup title="Urgent Attention" tier="critical" items={critical} defaultOpen onWhy={onWhy} />
      <TierGroup title="Please Check" tier="review" items={review} defaultOpen onWhy={onWhy} />
      <TierGroup title="General Information" tier="info" items={info} defaultOpen={false} onWhy={onWhy} />
      {alerts.length === 0 && (
        <p className="rounded-2xl border border-[#BBF7D0] bg-[#F0FDF4] px-4 py-3 text-sm text-[#15803D]">
          No alerts for resolved lines. This is not a clearance.
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
    <div className={`overflow-hidden rounded-2xl border bg-white ${m.border}`}>
      <button
        type="button"
        className={`flex w-full items-center justify-between gap-3 px-4 py-3 text-left ${m.bg}`}
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span className={`flex items-center gap-2 text-sm font-bold ${m.className}`}>
          <Icon className="h-4 w-4" aria-hidden />
          {title}
          <span className="rounded-full bg-white/80 px-2 py-0.5 text-xs">{items.length}</span>
        </span>
        <ChevronDown className={`h-4 w-4 text-[var(--muted)] transition ${open ? 'rotate-180' : ''}`} aria-hidden />
      </button>
      {open && (
        <ul className="space-y-2 border-t border-[var(--card-border)] p-3">
          {items.map((a) => (
            <li key={a.id} className="rounded-2xl border border-[var(--card-border)] bg-white p-4">
              <div className="flex items-start gap-3">
                <span className={`mt-0.5 rounded-lg p-1.5 ${m.bg} ${m.className}`}>
                  <Icon className="h-4 w-4" aria-hidden />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-semibold leading-snug text-[var(--heading)]">{a.title}</p>
                  <div className="mt-3 space-y-2 text-sm">
                    <p>
                      <span className="font-semibold text-[var(--heading)]">What we found: </span>
                      <span className="text-[var(--body)]">{a.reason}</span>
                    </p>
                    {a.mechanism && (
                      <p>
                        <span className="font-semibold text-[var(--heading)]">Why it matters: </span>
                        <span className="text-[var(--body)]">{String(a.mechanism)}</span>
                      </p>
                    )}
                    <p>
                      <span className="font-semibold text-[var(--heading)]">What you should do: </span>
                      <span className="text-[var(--body)]">{a.suggested_action}</span>
                    </p>
                    {(a.source_rule_id || a.source_label) && (
                      <p className="text-xs text-[var(--muted)]">
                        Evidence: {a.source_rule_id}
                        {a.source_label ? ` · ${a.source_label}` : ''}
                      </p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => onWhy(a)}
                    className="btn-secondary mt-3 px-3 py-1.5 text-xs"
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
