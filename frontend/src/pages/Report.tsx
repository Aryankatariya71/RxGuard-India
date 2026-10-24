import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type Report as ReportT } from '../api/hm02'
import { FindingCard } from '../components/findings/FindingCard'
import { BannerDisclaimer } from '../components/common/Disclaimer'

export function Report() {
  const { id } = useParams()
  const [report, setReport] = useState<ReportT | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    api
      .report(id)
      .then(setReport)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <p>Loading report…</p>
  if (error)
    return (
      <div className="card border-red-200 bg-red-50 p-4 text-red-800" role="alert">
        {error}
        <div className="mt-3">
          <Link to="/dashboard" className="btn-secondary text-xs">
            Back
          </Link>
        </div>
      </div>
    )
  if (!report) return null

  const s = report.summary || {}
  const findings = report.findings || []
  const groups: Record<string, typeof findings> = {
    critical: findings.filter((f) => ['CRITICAL', 'HIGH'].includes(f.severity)),
    interactions: findings.filter((f) => f.category === 'DRUG_DRUG_INTERACTION'),
    duplicates: findings.filter((f) => f.category === 'DUPLICATE_INGREDIENT'),
    dosage: findings.filter((f) =>
      [
        'DOSE_OUTSIDE_CONFIGURED_RANGE',
        'FREQUENCY_OUTSIDE_CONFIGURED_RANGE',
        'INSUFFICIENT_DOSAGE_INFORMATION',
        'UNIT_MISMATCH',
      ].includes(f.category),
    ),
    unresolved: findings.filter((f) => f.category === 'UNRESOLVED_PRODUCT'),
    other: findings.filter(
      (f) =>
        !['DRUG_DRUG_INTERACTION', 'DUPLICATE_INGREDIENT', 'UNRESOLVED_PRODUCT'].includes(
          f.category,
        ) &&
        ![
          'DOSE_OUTSIDE_CONFIGURED_RANGE',
          'FREQUENCY_OUTSIDE_CONFIGURED_RANGE',
          'INSUFFICIENT_DOSAGE_INFORMATION',
          'UNIT_MISMATCH',
        ].includes(f.category) &&
        !['CRITICAL', 'HIGH'].includes(f.severity),
    ),
  }

  return (
    <div className="space-y-6 print-report">
      <div className="no-print flex flex-wrap gap-2">
        <Link to="/history" className="btn-secondary text-xs">
          History
        </Link>
        <button type="button" className="btn-secondary text-xs" onClick={() => window.print()}>
          Print / PDF
        </button>
        <a className="btn-secondary text-xs" href={api.exportUrl(report.review.id, 'txt')}>
          Download TXT
        </a>
        <a className="btn-secondary text-xs" href={api.exportUrl(report.review.id, 'csv')}>
          Download CSV
        </a>
      </div>

      <header className="card p-5">
        <p className="text-xs font-semibold uppercase text-[var(--color-primary)]">Safety report</p>
        <h1 className="mt-1 text-2xl font-bold">{report.review.title || report.review.review_reference}</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          {report.review.review_reference} · {report.review.created_at} · status{' '}
          {report.review.status}
        </p>
        <p className="mt-4 text-lg font-semibold text-[var(--color-ink)]">
          {String(s.status_label || 'Review')}
        </p>
        <p className="mt-1 text-sm text-[var(--color-muted)]">{String(s.status_note || '')}</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-4">
          {(
            [
              ['Medicines', s.medicines_entered],
              ['Resolved', s.resolved_products],
              ['Unresolved', s.unresolved_products],
              ['Findings', s.total_findings],
            ] as [string, number | undefined][]
          ).map(([k, v]) => (
            <div key={k} className="rounded-xl bg-slate-50 p-3">
              <p className="text-xs text-[var(--color-muted)]">{k}</p>
              <p className="text-xl font-bold">{String(v ?? 0)}</p>
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-[var(--color-muted)]">
          Catalogue {String(s.catalogue_version)} · Rules {String(s.rule_set_version)}
        </p>
      </header>

      <BannerDisclaimer />

      <section className="card p-5">
        <h2 className="font-bold">Medicines reviewed</h2>
        <ul className="mt-3 space-y-2 text-sm">
          {report.items.map((it) => (
            <li key={it.id} className="rounded-xl border border-[var(--color-border)] p-3">
              <strong>{it.entered_brand_name}</strong>
              <span className="ml-2 text-xs text-[var(--color-muted)]">{it.resolution_status}</span>
              {it.product?.is_synthetic && (
                <span className="ml-2 badge border border-violet-200 bg-violet-50 text-violet-800">
                  SYNTHETIC
                </span>
              )}
              <p className="text-xs text-[var(--color-muted)]">
                {it.product?.ingredients?.map((i) => i.canonical_name).join(', ') ||
                  'Ingredients not resolved'}
              </p>
            </li>
          ))}
        </ul>
      </section>

      {(
        [
          ['High-priority findings', groups.critical],
          ['Interaction findings', groups.interactions],
          ['Duplicate ingredients', groups.duplicates],
          ['Dosage-related', groups.dosage],
          ['Unresolved medicines', groups.unresolved],
        ] as const
      ).map(([title, list]) =>
        list.length ? (
          <section key={title} className="space-y-3">
            <h2 className="text-lg font-bold">{title}</h2>
            {list.map((f) => (
              <FindingCard key={f.id} finding={f} />
            ))}
          </section>
        ) : null,
      )}

      <section className="card p-5 text-sm">
        <h2 className="font-bold">Recommended next steps</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-[var(--color-muted)]">
          <li>Discuss flagged findings with a qualified doctor or pharmacist.</li>
          <li>Do not start, stop, or change medication based only on this tool.</li>
          <li>Treat DEMO_ONLY / synthetic findings as demonstration labels only.</li>
        </ul>
      </section>
    </div>
  )
}
