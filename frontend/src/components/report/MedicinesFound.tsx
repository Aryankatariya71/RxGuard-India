import type { LineItem } from '../../api/types'
import { lineKey } from '../../lib/whatIf'

interface Props {
  items: LineItem[]
  prescriptionText?: string
  activeKeys?: Set<string>
  onToggleActive?: (key: string, next: boolean) => void
  onPickCandidate: (line: string, brandName: string) => void
}

export function MedicinesFound({
  items,
  prescriptionText,
  activeKeys,
  onToggleActive,
  onPickCandidate,
}: Props) {
  if (!items?.length) {
    return (
      <p className="text-sm text-[var(--muted)]">No medicine lines yet — run Analyze.</p>
    )
  }

  const rxLines = (prescriptionText || '').split('\n')

  return (
    <div className="print-report space-y-3">
      <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--muted)]">
        Medicines found
      </h3>
      <ul className="space-y-3">
        {items.map((item, idx) => {
          const status = (item.status || '').toLowerCase()
          const needs = !item.resolved || status === 'ambiguous' || status === 'not_found'
          const cand0 = (item.candidates || [])[0]
          const similarity =
            typeof cand0?.score === 'number' ? Math.round(Number(cand0.score)) : undefined

          let badge = 'exact'
          let badgeClass = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
          if (status === 'confident') {
            badge = similarity != null ? `fuzzy ${similarity}%` : 'fuzzy'
            badgeClass = 'bg-sky-500/15 text-sky-300 border-sky-500/30'
          } else if (status === 'ambiguous') {
            badge = 'ambiguous'
            badgeClass = 'bg-amber-500/15 text-amber-300 border-amber-500/30'
          } else if (status === 'not_found' || !item.resolved) {
            badge = 'not found'
            badgeClass = 'bg-rose-500/15 text-rose-300 border-rose-500/30'
          }

          // Map report item back to original rx line for what-if key
          const matchIdx = rxLines.findIndex(
            (l) => l.trim() && (l.trim() === (item.line || '').trim() || l.includes((item.line || '').slice(0, 12))),
          )
          const key =
            matchIdx >= 0
              ? lineKey(rxLines[matchIdx], matchIdx)
              : lineKey(item.line || '', idx)
          const enabled = activeKeys ? activeKeys.has(key) : true

          return (
            <li
              key={`${item.line}-${idx}`}
              className={`glass rounded-2xl p-4 transition ${enabled ? '' : 'opacity-50'}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="font-mono text-xs text-[var(--muted)]">{item.line}</p>
                  <p className="mt-1 text-base font-semibold">
                    {item.matched_brand || 'Needs confirmation'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {onToggleActive && (
                    <label className="flex cursor-pointer items-center gap-2 text-[11px] text-[var(--muted)]">
                      <span className="sr-only">Include in what-if analysis</span>
                      <input
                        type="checkbox"
                        role="switch"
                        aria-checked={enabled}
                        checked={enabled}
                        onChange={(e) => onToggleActive(key, e.target.checked)}
                        className="h-4 w-8 cursor-pointer appearance-none rounded-full bg-slate-600 transition checked:bg-teal-500"
                        style={{
                          backgroundImage: enabled
                            ? 'radial-gradient(circle at 75% 50%, white 40%, transparent 45%)'
                            : 'radial-gradient(circle at 25% 50%, white 40%, transparent 45%)',
                        }}
                      />
                      {enabled ? 'On' : 'Off'}
                    </label>
                  )}
                  <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${badgeClass}`}>
                    {badge}
                  </span>
                </div>
              </div>

              {(item.ingredients || []).length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {(item.ingredients || []).map((ing, i) => {
                    const name = ing.ingredient || '?'
                    const sv = ing.strength_value
                    const unit = ing.unit || ''
                    const label =
                      sv != null ? `${name} ${sv}${unit ? ` ${unit}` : ''}` : name
                    return (
                      <span
                        key={`${name}-${i}`}
                        className="rounded-lg border border-indigo-400/20 bg-indigo-500/10 px-2 py-1 font-mono text-[11px] text-indigo-200"
                      >
                        {label}
                      </span>
                    )
                  })}
                </div>
              )}

              {needs && (item.candidates || []).length > 0 && (
                <div className="mt-3">
                  <p className="mb-2 text-xs font-semibold text-amber-300">
                    Needs confirmation — pick a candidate
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {(item.candidates || []).slice(0, 5).map((c) => (
                      <button
                        key={`${c.brand_id}-${c.name}`}
                        type="button"
                        onClick={() =>
                          onPickCandidate(item.line || '', String(c.name || ''))
                        }
                        className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-xs font-medium text-amber-100 transition hover:bg-amber-500/20"
                      >
                        {c.name}
                        {typeof c.score === 'number'
                          ? ` (${Math.round(Number(c.score))}%)`
                          : ''}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {needs && !(item.candidates || []).length && (
                <p className="mt-2 text-xs text-rose-300">Needs confirmation — no candidates</p>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
