import { X } from 'lucide-react'
import type { Alert, DailyIngredient } from '../../api/types'
import { tierMeta } from '../../lib/severity'

interface Props {
  alert: Alert | null
  doses: DailyIngredient[]
  onClose: () => void
}

export function WhyDrawer({ alert, doses, onClose }: Props) {
  if (!alert) return null
  const m = tierMeta(alert.tier)
  const Icon = m.icon

  const doseLines = (alert.ingredients || []).flatMap((ing) => {
    const row = doses.find((d) => d.ingredient === ing)
    if (!row) return []
    const parts = (row.contributions || []).map(
      (c) => `${c.brand}: ${c.mg_per_day} mg`,
    )
    const sum = `${parts.join(' + ')} = ${row.total_mg_per_day} mg`
    return [{ ing, sum, limit: alert.limit_mg_day, pct: alert.percent }]
  })

  const isDraft =
    /draft/i.test(alert.reason || '') ||
    /pending pharmacist/i.test(alert.reason || '') ||
    String(alert.source_label || '').includes('max_dose') ||
    String(alert.source_label || '').startsWith('curated')

  return (
    <div className="no-print fixed inset-0 z-[80] flex justify-end" role="dialog" aria-modal aria-label="Rule trace">
      <button
        type="button"
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        aria-label="Close drawer"
        onClick={onClose}
      />
      <aside className="glass relative z-10 flex h-full w-full max-w-md flex-col overflow-y-auto border-l border-[var(--card-border)] p-5 shadow-2xl">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <span className={`mt-0.5 rounded-xl p-2 ${m.bg} ${m.className}`}>
              <Icon className="h-5 w-5" aria-hidden />
            </span>
            <div>
              <p className={`text-xs font-semibold uppercase ${m.className}`}>{m.label}</p>
              <h3 className="text-lg font-bold leading-snug">{alert.title}</h3>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl p-2 hover:bg-[#F1F7F5]"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <dl className="space-y-4 text-sm">
          <div>
            <dt className="text-xs uppercase tracking-wider text-[var(--muted)]">Rule id</dt>
            <dd className="mt-1 font-mono text-[#123C38]">{alert.source_rule_id}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-[var(--muted)]">Source</dt>
            <dd className="mt-1 font-mono text-sm break-all">{alert.source_label}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-[var(--muted)]">Reason</dt>
            <dd className="mt-1 text-[var(--fg)]">{alert.reason}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wider text-[var(--muted)]">Suggested action</dt>
            <dd className="mt-1">{alert.suggested_action}</dd>
          </div>
          {doseLines.length > 0 && (
            <div>
              <dt className="text-xs uppercase tracking-wider text-[var(--muted)]">Numbers used</dt>
              <dd className="mt-1 space-y-2">
                {doseLines.map((d) => (
                  <p key={d.ing} className="rounded-xl bg-[#F8FBFA] p-3 font-mono text-xs leading-relaxed">
                    <span className="text-[#123C38]">{d.ing}</span>
                    <br />
                    {d.sum}
                    {d.limit != null && (
                      <>
                        <br />
                        limit {d.limit} mg/day
                        {d.pct != null ? ` (${Math.round(d.pct)}%)` : ''}
                      </>
                    )}
                  </p>
                ))}
              </dd>
            </div>
          )}
        </dl>

        {isDraft && (
          <p className="mt-6 rounded-xl border border-[#FED7AA] bg-[#FFF7ED] px-3 py-2 text-xs font-medium text-[#B45309]">
            DRAFT, pending pharmacist verification
          </p>
        )}
      </aside>
    </div>
  )
}
