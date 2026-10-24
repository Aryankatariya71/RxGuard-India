import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Medicine } from '../api/hm02'
import { DEMO_LABEL } from '../lib/copy'

export function Medicines() {
  const [q, setQ] = useState('DEMO')
  const [searchBy, setSearchBy] = useState('brand')
  const [form, setForm] = useState('')
  const [status, setStatus] = useState('')
  const [items, setItems] = useState<Medicine[]>([])
  const [total, setTotal] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Medicine | null>(null)

  const load = () => {
    setError(null)
    api
      .medicines({
        q,
        search_by: searchBy,
        dosage_form: form || undefined,
        catalogue_status: status || undefined,
        page_size: 50,
      })
      .then((r) => {
        setItems(r.items)
        setTotal(r.total)
      })
      .catch((e) => setError(e.message))
  }

  useEffect(load, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Medicine catalogue</h1>
      <p className="text-sm text-[var(--color-muted)]">{DEMO_LABEL}</p>

      <div className="card grid gap-3 p-4 sm:grid-cols-4">
        <input className="input sm:col-span-2" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search" />
        <select className="input" value={searchBy} onChange={(e) => setSearchBy(e.target.value)}>
          <option value="brand">Brand</option>
          <option value="generic">Generic / ingredient text</option>
          <option value="strength">Strength</option>
        </select>
        <button type="button" className="btn-primary" onClick={load}>
          Search
        </button>
        <select className="input" value={form} onChange={(e) => setForm(e.target.value)}>
          <option value="">All forms</option>
          <option value="tablet">tablet</option>
          <option value="capsule">capsule</option>
          <option value="syrup">syrup</option>
        </select>
        <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="synthetic">synthetic</option>
          <option value="source_backed">source_backed</option>
          <option value="unverified">unverified</option>
        </select>
      </div>

      {error && (
        <div className="card border-red-200 bg-red-50 p-3 text-red-800" role="alert">
          {error}
          <button type="button" className="btn-secondary ml-2 text-xs" onClick={load}>
            Retry
          </button>
        </div>
      )}

      <p className="text-sm text-[var(--color-muted)]">{total} products</p>
      <div className="grid gap-4 lg:grid-cols-2">
        <ul className="space-y-2">
          {items.map((m) => (
            <li key={m.id}>
              <button
                type="button"
                className="card w-full p-4 text-left hover:border-blue-300"
                onClick={() => setSelected(m)}
              >
                <p className="font-semibold">{m.brand_name}</p>
                <p className="text-sm text-[var(--color-muted)]">{m.generic_display_name}</p>
                <p className="mt-1 text-xs">
                  {m.dosage_form} · {m.catalogue_status}
                  {m.is_synthetic ? ' · SYNTHETIC' : ''}
                </p>
              </button>
            </li>
          ))}
        </ul>
        <div className="card p-5">
          {selected ? (
            <>
              <h2 className="text-lg font-bold">{selected.brand_name}</h2>
              <p className="text-sm text-[var(--color-muted)]">{selected.generic_display_name}</p>
              <p className="mt-2 text-sm">Form: {selected.dosage_form}</p>
              <p className="text-sm">Route: {selected.route || '—'}</p>
              <p className="text-sm">Manufacturer: {selected.manufacturer || 'Not provided in demo seed'}</p>
              <p className="mt-2 text-sm">Source: {selected.source_name}</p>
              <p className="text-xs text-[var(--color-muted)]">Status: {selected.catalogue_status}</p>
              <h3 className="mt-4 font-semibold">Ingredients</h3>
              <ul className="mt-2 space-y-1 text-sm">
                {selected.ingredients.map((i) => (
                  <li key={i.id}>
                    {i.canonical_name}
                    {i.ingredient_strength != null
                      ? ` ${i.ingredient_strength} ${i.strength_unit || ''}`
                      : ''}
                    {i.is_synthetic ? ' (synthetic)' : ''}
                  </li>
                ))}
              </ul>
              <Link to="/review/new" className="btn-primary mt-4 inline-flex text-xs">
                Start a review
              </Link>
            </>
          ) : (
            <p className="text-sm text-[var(--color-muted)]">Select a product to view details.</p>
          )}
        </div>
      </div>
    </div>
  )
}
