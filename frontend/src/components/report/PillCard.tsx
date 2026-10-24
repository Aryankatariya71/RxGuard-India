import { useMemo, useState } from 'react'
import type { AnalyzeResponse } from '../../api/types'
import {
  buildPillCard,
  SLOT_LABELS_EN,
  SLOT_LABELS_HI,
  SLOT_ORDER,
} from '../../lib/pillCard'

interface Props {
  report: AnalyzeResponse
  onClose?: () => void
}

export function PillCard({ report, onClose }: Props) {
  const [lang, setLang] = useState<'en' | 'hi'>('en')
  const data = useMemo(() => buildPillCard(report.items || []), [report.items])
  const labels = lang === 'hi' ? SLOT_LABELS_HI : SLOT_LABELS_EN

  const printCard = () => {
    window.print()
  }

  return (
    <div className="pill-card-root space-y-4" data-testid="pill-card">
      <div className="no-print flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--muted)]">
          Patient pill card
        </h3>
        <div className="flex flex-wrap gap-2">
          <div className="inline-flex rounded-xl border border-white/10 p-0.5 text-[11px]">
            <button
              type="button"
              className={`rounded-lg px-2 py-1 ${lang === 'en' ? 'bg-teal-500/20 text-teal-200' : 'text-[var(--muted)]'}`}
              onClick={() => setLang('en')}
              aria-pressed={lang === 'en'}
            >
              English
            </button>
            <button
              type="button"
              className={`rounded-lg px-2 py-1 ${lang === 'hi' ? 'bg-teal-500/20 text-teal-200' : 'text-[var(--muted)]'}`}
              onClick={() => setLang('hi')}
              aria-pressed={lang === 'hi'}
            >
              हिंदी
            </button>
          </div>
          <button
            type="button"
            onClick={printCard}
            className="rounded-xl border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-semibold"
          >
            Print A4
          </button>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-white/15 px-3 py-1.5 text-xs"
            >
              Close
            </button>
          )}
        </div>
      </div>

      <div className="pill-card-sheet glass rounded-2xl p-4 sm:p-6">
        <header className="mb-4 border-b border-[var(--card-border)] pb-3">
          <p className="text-lg font-bold tracking-tight sm:text-2xl">RxGuard India — Pill card</p>
          <p className="text-xs text-[var(--muted)]">
            Schedule taken from the written prescription only.
          </p>
        </header>

        <div className="overflow-x-auto">
          <table className="pill-card-table w-full border-collapse text-left">
            <thead>
              <tr>
                <th className="pill-th">Medicine</th>
                {SLOT_ORDER.map((s) => (
                  <th key={s} className="pill-th">
                    <span className="block">{labels[s]}</span>
                    {lang === 'hi' && (
                      <span className="block text-[10px] font-normal opacity-70">
                        {SLOT_LABELS_EN[s]}
                      </span>
                    )}
                    {lang === 'en' && (
                      <span className="block text-[10px] font-normal opacity-70">
                        {SLOT_LABELS_HI[s]}
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <tr key={row.brand + row.frequencyNote}>
                  <td className="pill-td">
                    <p className="pill-brand">{row.brand}</p>
                    <p className="pill-ings">{row.ingredientsLabel}</p>
                    {row.duration && (
                      <p className="text-[11px] text-[var(--muted)]">Duration: {row.duration}</p>
                    )}
                  </td>
                  {SLOT_ORDER.map((s) => (
                    <td key={s} className="pill-td pill-dose">
                      {row.slots[s] || '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {data.asNeeded.length > 0 && (
          <section className="mt-4">
            <h4 className="text-sm font-bold">As needed</h4>
            <ul className="mt-1 space-y-1 text-sm">
              {data.asNeeded.map((a) => (
                <li key={a.brand + a.instruction}>
                  <span className="font-semibold">{a.brand}</span>
                  {a.ingredientsLabel !== '—' && (
                    <span className="text-[var(--muted)]"> ({a.ingredientsLabel})</span>
                  )}
                  : {a.instruction}
                </li>
              ))}
            </ul>
          </section>
        )}

        {data.needsConfirmation.length > 0 && (
          <section className="mt-4">
            <h4 className="text-sm font-bold">Needs confirmation</h4>
            <ul className="mt-1 space-y-1 text-sm text-amber-800 dark:text-amber-100">
              {data.needsConfirmation.map((n) => (
                <li key={n.line}>
                  {n.line} — {n.reason}
                </li>
              ))}
            </ul>
          </section>
        )}

        <footer className="pill-footer mt-6 border-t border-[var(--card-border)] pt-3 text-xs leading-relaxed text-[var(--muted)]">
          {data.footer}
        </footer>
      </div>
    </div>
  )
}
