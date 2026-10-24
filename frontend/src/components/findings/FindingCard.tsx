import { useState } from 'react'
import { AlertTriangle, ChevronDown, Info, ShieldAlert } from 'lucide-react'
import type { Finding } from '../../api/hm02'
import { SHORT } from '../../lib/copy'

function sevStyle(sev: string) {
  switch (sev) {
    case 'CRITICAL':
    case 'HIGH':
      return {
        icon: ShieldAlert,
        cls: 'border-red-200 bg-red-50 text-red-800',
        label: sev,
      }
    case 'MODERATE':
      return {
        icon: AlertTriangle,
        cls: 'border-amber-200 bg-amber-50 text-amber-900',
        label: sev,
      }
    default:
      return { icon: Info, cls: 'border-slate-200 bg-slate-50 text-slate-700', label: sev }
  }
}

export function FindingCard({ finding }: { finding: Finding }) {
  const [open, setOpen] = useState(false)
  const s = sevStyle(finding.severity)
  const Icon = s.icon
  return (
    <article className={`card border p-4 ${s.cls.split(' ').slice(0, 2).join(' ')}`}>
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`badge border ${s.cls}`}>{s.label}</span>
            <span className="badge border border-slate-200 bg-white text-slate-600">
              {finding.category}
            </span>
            {finding.is_synthetic && (
              <span className="badge border border-violet-200 bg-violet-50 text-violet-800">
                DEMO_ONLY
              </span>
            )}
            <span className="badge border border-slate-200 bg-white text-slate-600">
              {finding.evidence_status}
            </span>
          </div>
          <h3 className="mt-2 font-semibold text-[var(--color-ink)]">{finding.title}</h3>
          <p className="mt-1 text-sm text-[var(--color-muted)]">{finding.description}</p>
          {finding.affected_brand_names?.length > 0 && (
            <p className="mt-2 text-xs text-[var(--color-muted)]">
              Medicines: {finding.affected_brand_names.join(', ')}
            </p>
          )}
          <p className="mt-2 text-sm">
            <strong>Next step:</strong> {finding.recommended_next_step}
          </p>
          <p className="mt-2 text-xs text-[var(--color-muted)]">{SHORT}</p>
          <button
            type="button"
            className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-[var(--color-primary)]"
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
          >
            Why was this flagged?
            <ChevronDown className={`h-4 w-4 transition ${open ? 'rotate-180' : ''}`} />
          </button>
          {open && (
            <dl className="mt-3 space-y-2 rounded-xl bg-white/80 p-3 text-sm">
              <div>
                <dt className="text-xs uppercase text-[var(--color-muted)]">Rule</dt>
                <dd className="font-mono">
                  {finding.rule_id || '—'} · {finding.rule_version || '—'}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-[var(--color-muted)]">Source</dt>
                <dd>{finding.source_reference || '—'}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-[var(--color-muted)]">Limitations</dt>
                <dd>{finding.limitations || '—'}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-[var(--color-muted)]">Evaluation</dt>
                <dd>{finding.evaluation_status}</dd>
              </div>
            </dl>
          )}
        </div>
      </div>
    </article>
  )
}
