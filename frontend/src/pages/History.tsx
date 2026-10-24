import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Review } from '../api/hm02'

export function History() {
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('')
  const [items, setItems] = useState<Review[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    setError(null)
    api
      .listReviews({ q, status: status || undefined, page_size: 50 })
      .then((r) => setItems(r.items))
      .catch((e) => setError(e.message))
  }

  useEffect(load, [])

  const remove = async (id: string) => {
    if (!confirm('Delete this review permanently?')) return
    await api.deleteReview(id)
    load()
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Review history</h1>
      <div className="flex flex-wrap gap-2">
        <input className="input max-w-xs" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search reference or title" />
        <select className="input max-w-[160px]" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="draft">draft</option>
          <option value="evaluated">evaluated</option>
          <option value="incomplete">incomplete</option>
        </select>
        <button type="button" className="btn-primary" onClick={load}>
          Filter
        </button>
      </div>
      {error && (
        <div className="card border-red-200 bg-red-50 p-3 text-red-800" role="alert">
          {error}
        </div>
      )}
      <ul className="space-y-2">
        {items.map((r) => (
          <li key={r.id} className="card flex flex-wrap items-center justify-between gap-3 p-4">
            <div>
              <p className="font-semibold">{r.title || r.review_reference}</p>
              <p className="text-xs text-[var(--color-muted)]">
                {r.review_reference} · {r.status} · {r.item_count || 0} meds ·{' '}
                {r.finding_count || 0} findings
              </p>
            </div>
            <div className="flex gap-2">
              <Link to={`/reviews/${r.id}`} className="btn-secondary text-xs">
                Open
              </Link>
              <a className="btn-secondary text-xs" href={api.exportUrl(r.id)}>
                Export
              </a>
              <button type="button" className="btn-secondary text-xs text-red-700" onClick={() => remove(r.id)}>
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>
      {items.length === 0 && !error && (
        <p className="text-sm text-[var(--color-muted)]">No reviews stored yet.</p>
      )}
    </div>
  )
}
