import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Review } from '../api/hm02'
import { DEMO_LABEL } from '../lib/copy'

export function Dashboard() {
  const [reviews, setReviews] = useState<Review[]>([])
  const [total, setTotal] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [dataStatus, setDataStatus] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    setError(null)
    Promise.all([api.listReviews({ page_size: 10 }), api.dataStatus()])
      .then(([r, d]) => {
        setReviews(r.items)
        setTotal(r.total)
        setDataStatus(d)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const meds = reviews.reduce((a, r) => a + (r.item_count || 0), 0)
  const findings = reviews.reduce((a, r) => a + (r.finding_count || 0), 0)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-[var(--color-muted)]">Welcome to RxGuard India (demo mode, no multi-user auth).</p>
        </div>
        <Link to="/review/new" className="btn-primary">
          New Prescription Review
        </Link>
      </div>

      {error && (
        <div className="card border-red-200 bg-red-50 p-4 text-red-800" role="alert">
          <p className="font-semibold">Service unavailable</p>
          <p className="text-sm">{error}</p>
          <button type="button" className="btn-secondary mt-3" onClick={load}>
            Retry
          </button>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="card p-4">
          <p className="text-xs uppercase text-[var(--color-muted)]">Saved reviews</p>
          <p className="mt-1 text-3xl font-bold">{loading ? '—' : total}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase text-[var(--color-muted)]">Medicines in recent list</p>
          <p className="mt-1 text-3xl font-bold">{loading ? '—' : meds}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase text-[var(--color-muted)]">Findings in recent list</p>
          <p className="mt-1 text-3xl font-bold">{loading ? '—' : findings}</p>
        </div>
      </div>

      {dataStatus && (
        <div className="card p-4 text-sm">
          <p className="font-semibold">Data source status</p>
          <p className="mt-1 text-[var(--color-muted)]">
            Catalogue {String(dataStatus.catalogue_version)} · synthetic products{' '}
            {String(dataStatus.synthetic_product_count)} · {DEMO_LABEL}
          </p>
        </div>
      )}

      <section className="card p-4">
        <h2 className="font-bold">Recent reviews</h2>
        {!loading && reviews.length === 0 && (
          <p className="mt-4 text-sm text-[var(--color-muted)]">
            No saved reviews yet. Start a new review or load a synthetic demo scenario.
          </p>
        )}
        <ul className="mt-3 divide-y divide-[var(--color-border)]">
          {reviews.map((r) => (
            <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
              <div>
                <p className="font-medium">{r.title || r.review_reference}</p>
                <p className="text-xs text-[var(--color-muted)]">
                  {r.review_reference} · {r.status} · {r.item_count || 0} medicines
                </p>
              </div>
              <Link to={`/reviews/${r.id}`} className="btn-secondary text-xs">
                Open report
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
