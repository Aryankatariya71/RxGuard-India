import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type Medicine, type Review, type ReviewItem } from '../api/hm02'
import { DEMO_LABEL } from '../lib/copy'

const SCENARIOS = [
  { id: 'duplicate', title: 'Duplicate ingredient' },
  { id: 'interaction', title: 'Synthetic interaction' },
  { id: 'missing_dose', title: 'Missing dosage information' },
  { id: 'unresolved', title: 'Unresolved brand' },
  { id: 'combination', title: 'Combination product' },
]

export function NewReview() {
  const nav = useNavigate()
  const [step, setStep] = useState(0)
  const [review, setReview] = useState<Review | null>(null)
  const [title, setTitle] = useState('')
  const [patientRef, setPatientRef] = useState('')
  const [age, setAge] = useState<number | ''>('')
  const [q, setQ] = useState('')
  const [results, setResults] = useState<Medicine[]>([])
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [items, setItems] = useState<ReviewItem[]>([])

  const canEvaluate = useMemo(() => (items?.length || 0) > 0 && !!review, [items, review])

  const ensureReview = async () => {
    if (review) return review
    const r = await api.createReview({
      title: title || 'Untitled review',
      patient_reference: patientRef || null,
      age_years: age === '' ? null : Number(age),
    })
    setReview(r)
    return r
  }

  const search = async () => {
    setSearching(true)
    setError(null)
    try {
      const r = await api.medicines({ q, page_size: 20 })
      setResults(r.items)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSearching(false)
    }
  }

  const addMedicine = async (m: Medicine) => {
    setBusy(true)
    setError(null)
    try {
      const r = await ensureReview()
      const item = await api.addItem(r.id, {
        product_id: m.id,
        entered_brand_name: m.brand_name,
        dose_amount: 1,
        dose_unit: m.dosage_form === 'syrup' ? 'ml' : 'tablet',
        frequency_value: 2,
        frequency_unit: 'per_day',
        route: m.route || 'oral',
      })
      const fresh = await api.getReview(r.id)
      setReview(fresh)
      setItems(fresh.items || [])
      setStep(2)
      void item
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const updateDose = async (item: ReviewItem, patch: object) => {
    if (!review) return
    const updated = await api.updateItem(review.id, item.id, patch)
    setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)))
  }

  const removeItem = async (id: string) => {
    if (!review) return
    await api.deleteItem(review.id, id)
    setItems((prev) => prev.filter((i) => i.id !== id))
  }

  const run = async () => {
    if (!review) return
    setBusy(true)
    setError(null)
    try {
      await api.evaluate(review.id)
      nav(`/reviews/${review.id}`)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const loadScenario = async (id: string) => {
    setBusy(true)
    setError(null)
    try {
      const r = await api.demoScenario(id)
      nav(`/reviews/${r.review.id}`)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">New prescription review</h1>
      <p className="text-sm text-[var(--color-muted)]">
        Multi-step workflow. Demo mode — no authentication isolation.
      </p>

      <div className="card p-4">
        <h2 className="font-semibold">Load synthetic demo scenario</h2>
        <p className="mt-1 text-xs text-[var(--color-muted)]">{DEMO_LABEL}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {SCENARIOS.map((s) => (
            <button
              key={s.id}
              type="button"
              className="btn-secondary text-xs"
              disabled={busy}
              onClick={() => loadScenario(s.id)}
            >
              {s.title}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="card border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">
          {error}
        </div>
      )}

      <ol className="flex flex-wrap gap-2 text-sm">
        {['Review info', 'Add medicines', 'Configure use', 'Summary'].map((label, i) => (
          <li key={label}>
            <button
              type="button"
              className={`rounded-full px-3 py-1 ${
                step === i
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'bg-slate-100 text-[var(--color-muted)]'
              }`}
              onClick={() => setStep(i)}
            >
              {i + 1}. {label}
            </button>
          </li>
        ))}
      </ol>

      {step === 0 && (
        <div className="card space-y-4 p-5">
          <label className="block text-sm">
            Review title (optional)
            <input className="input mt-1" value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>
          <label className="block text-sm">
            Patient reference (pseudonymous, optional)
            <input
              className="input mt-1"
              value={patientRef}
              onChange={(e) => setPatientRef(e.target.value)}
              placeholder="e.g. DEMO-PATIENT"
            />
          </label>
          <label className="block text-sm">
            Age in years (needed for some dosage rules)
            <input
              className="input mt-1"
              type="number"
              min={0}
              max={120}
              value={age}
              onChange={(e) => setAge(e.target.value === '' ? '' : Number(e.target.value))}
            />
          </label>
          <p className="text-xs text-[var(--color-muted)]">
            We do not infer conditions from medicines. Missing age is not treated as a negative finding.
          </p>
          <button
            type="button"
            className="btn-primary"
            onClick={async () => {
              setBusy(true)
              try {
                await ensureReview()
                setStep(1)
              } catch (e) {
                setError((e as Error).message)
              } finally {
                setBusy(false)
              }
            }}
          >
            Continue
          </button>
        </div>
      )}

      {step === 1 && (
        <div className="card space-y-4 p-5">
          <div className="flex gap-2">
            <input
              className="input"
              placeholder="Search DEMO brands or ingredients"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && search()}
            />
            <button type="button" className="btn-primary" onClick={search} disabled={searching}>
              {searching ? 'Searching…' : 'Search'}
            </button>
          </div>
          <ul className="space-y-2">
            {results.map((m) => (
              <li key={m.id} className="flex flex-wrap items-start justify-between gap-2 rounded-xl border border-[var(--color-border)] p-3">
                <div>
                  <p className="font-semibold">{m.brand_name}</p>
                  <p className="text-sm text-[var(--color-muted)]">{m.generic_display_name}</p>
                  <p className="mt-1 text-xs">
                    {m.dosage_form} · {m.catalogue_status}
                    {m.is_synthetic ? ' · SYNTHETIC' : ''}
                  </p>
                  <p className="text-xs text-[var(--color-muted)]">
                    Ingredients:{' '}
                    {m.ingredients.map((i) => i.canonical_name).join(', ') || '—'}
                  </p>
                </div>
                <button type="button" className="btn-secondary text-xs" disabled={busy} onClick={() => addMedicine(m)}>
                  Add
                </button>
              </li>
            ))}
          </ul>
          {results.length === 0 && (
            <p className="text-sm text-[var(--color-muted)]">Search the synthetic catalogue to add medicines.</p>
          )}
          <button type="button" className="btn-secondary" onClick={() => setStep(2)}>
            Configure doses →
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="card space-y-4 p-5">
          {items.length === 0 && (
            <p className="text-sm text-[var(--color-muted)]">No medicines yet. Go back and add products.</p>
          )}
          {items.map((it) => (
            <div key={it.id} className="rounded-xl border border-[var(--color-border)] p-3">
              <div className="flex justify-between gap-2">
                <p className="font-semibold">{it.entered_brand_name}</p>
                <button type="button" className="text-xs text-red-700" onClick={() => removeItem(it.id)}>
                  Remove
                </button>
              </div>
              <p className="text-xs text-[var(--color-muted)]">Resolution: {it.resolution_status}</p>
              <div className="mt-2 grid gap-2 sm:grid-cols-3">
                <label className="text-xs">
                  Dose amount
                  <input
                    className="input mt-1"
                    type="number"
                    defaultValue={it.dose_amount ?? ''}
                    onBlur={(e) =>
                      updateDose(it, {
                        dose_amount: e.target.value === '' ? null : Number(e.target.value),
                      })
                    }
                  />
                </label>
                <label className="text-xs">
                  Unit
                  <input
                    className="input mt-1"
                    defaultValue={it.dose_unit ?? ''}
                    onBlur={(e) => updateDose(it, { dose_unit: e.target.value || null })}
                  />
                </label>
                <label className="text-xs">
                  Times / day
                  <input
                    className="input mt-1"
                    type="number"
                    defaultValue={it.frequency_value ?? ''}
                    onBlur={(e) =>
                      updateDose(it, {
                        frequency_value: e.target.value === '' ? null : Number(e.target.value),
                      })
                    }
                  />
                </label>
              </div>
            </div>
          ))}
          <button type="button" className="btn-primary" onClick={() => setStep(3)}>
            Review summary →
          </button>
        </div>
      )}

      {step === 3 && (
        <div className="card space-y-4 p-5">
          <h2 className="font-bold">Summary</h2>
          <ul className="space-y-2 text-sm">
            {items.map((it) => (
              <li key={it.id}>
                <strong>{it.entered_brand_name}</strong> — {it.resolution_status}
                {it.product?.ingredients?.length
                  ? ` · ${it.product.ingredients.map((i) => i.canonical_name).join(', ')}`
                  : ' · unresolved ingredients'}
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="btn-primary"
            disabled={!canEvaluate || busy}
            onClick={run}
          >
            {busy ? 'Running…' : 'Run Safety Review'}
          </button>
        </div>
      )}
    </div>
  )
}
