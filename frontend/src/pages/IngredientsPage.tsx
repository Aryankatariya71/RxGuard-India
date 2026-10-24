import { useEffect, useRef, useState } from 'react'
import { ErrorBoundary } from '../components/common/ErrorBoundary'
import { AppLayout } from '../components/layout/AppLayout'
import {
  fetchIngredientProducts,
  searchIngredients,
  type IngredientHit,
  type IngredientProductsResponse,
} from '../api/ingredients'

export function IngredientsPage() {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<IngredientHit[]>([])
  const [starters, setStarters] = useState<IngredientHit[]>([])
  const [selected, setSelected] = useState<IngredientHit | null>(null)
  const [report, setReport] = useState<IngredientProductsResponse | null>(null)
  const [page, setPage] = useState(1)
  const [brandQ, setBrandQ] = useState('')
  const [formFilter, setFormFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [noMatch, setNoMatch] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    void searchIngredients('', 12).then((items) => {
      setStarters(items)
      if (!items.length) {
        setError(
          'No ingredients in the database yet. Seed the catalogue, or use demo data (Synthetic Ingredient X).',
        )
      }
    })
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (selected && selected.canonical_name === query) {
      setSuggestions([])
      setNoMatch(false)
      return
    }
    if (!query.trim()) {
      setSuggestions([])
      setNoMatch(false)
      return
    }
    setSearching(true)
    debounceRef.current = setTimeout(() => {
      void searchIngredients(query, 15).then((items) => {
        setSuggestions(items)
        setNoMatch(items.length === 0)
        setSearching(false)
      })
    }, 280)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query, selected])

  useEffect(() => {
    if (!selected) {
      setReport(null)
      return
    }
    setLoading(true)
    setError(null)
    void fetchIngredientProducts(selected.id, {
      page,
      page_size: 50,
      q: brandQ || undefined,
      dosage_form: formFilter || undefined,
    }).then((data) => {
      if (!data) {
        setError('Could not load products for this ingredient (API offline or not found).')
        setReport(null)
      } else {
        setReport(data)
      }
      setLoading(false)
    })
  }, [selected, page, brandQ, formFilter])

  const pick = (hit: IngredientHit) => {
    setSelected(hit)
    setQuery(hit.canonical_name)
    setSuggestions([])
    setNoMatch(false)
    setPage(1)
    setError(null)
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && suggestions[0]) {
      e.preventDefault()
      pick(suggestions[0])
    }
  }

  return (
    <AppLayout title="Hidden ingredient finder" subtitle="Catalogue brands sharing an ingredient">
    <div className="rx-container max-w-5xl py-10" data-testid="ingredients-page">
        <ErrorBoundary label="Hidden ingredient finder">
          <h1 className="text-3xl font-extrabold tracking-tight text-[#123C38]">
            Hidden ingredient finder
          </h1>
          <p className="mt-2 text-[#64748B]">
            See which catalogue brands share an ingredient — decision support only.
          </p>

          <div className="relative mt-6">
            <label htmlFor="ing-search" className="text-sm font-semibold">
              Search ingredient
            </label>
            <input
              id="ing-search"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value)
                setSelected(null)
              }}
              onKeyDown={onKeyDown}
              placeholder="Type a name, or pick a starter below"
              className="rx-input mt-2 w-full px-4 py-3 text-sm"
              autoComplete="off"
              role="combobox"
              aria-expanded={suggestions.length > 0}
              aria-controls="ing-suggestions"
            />
            {searching && (
              <p className="mt-1 text-xs text-[var(--muted)]">Searching…</p>
            )}
            {noMatch && (
              <p className="mt-2 text-sm text-[#B45309]" role="status">
                No ingredients match “{query}”. Try a starter chip below, or seed the A–Z
                catalogue into the DB.
              </p>
            )}
            {suggestions.length > 0 && (
              <ul
                id="ing-suggestions"
                role="listbox"
                className="absolute z-20 mt-1 max-h-60 w-full overflow-auto rounded-2xl border border-[var(--card-border)] bg-[var(--bg)] shadow-xl"
              >
                {suggestions.map((s) => (
                  <li key={s.id}>
                    <button
                      type="button"
                      role="option"
                      className="w-full px-4 py-2.5 text-left text-sm hover:bg-[#ECFDF5]"
                      onClick={() => pick(s)}
                    >
                      {s.canonical_name}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {!selected && starters.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
                Try one of these
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {starters.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => pick(s)}
                    className="rounded-full border border-[#DCE8E4] bg-[#ECFDF5] px-3 py-1.5 text-xs font-medium text-[#123C38] hover:bg-[#D1FAE5]"
                  >
                    {s.canonical_name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && (
            <p className="mt-4 text-sm text-[#B45309]" role="alert">
              {error}
            </p>
          )}

          {loading && (
            <p className="mt-6 text-sm text-[var(--muted)]">Loading catalogue counts…</p>
          )}

          {report && !loading && (
            <div className="mt-8 space-y-6">
              <p className="text-xs text-[var(--muted)]">{report.caption}</p>
              <div className="grid gap-3 sm:grid-cols-3">
                <Stat label="Products containing it" value={report.total_products} />
                <Stat label="Single-ingredient" value={report.single_ingredient} />
                <Stat label="Combination products" value={report.combination} />
              </div>

              <section>
                <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--muted)]">
                  By dosage form
                </h2>
                <ul className="mt-2 flex flex-wrap gap-2">
                  {Object.entries(report.by_dosage_form).map(([form, n]) => (
                    <li key={form}>
                      <button
                        type="button"
                        onClick={() => {
                          setFormFilter(formFilter === form ? '' : form)
                          setPage(1)
                        }}
                        className={`rounded-full border px-3 py-1 text-xs ${
                          formFilter === form
                            ? 'border-[#0D9B78] bg-[#ECFDF5]'
                            : 'border-[var(--card-border)] bg-white'
                        }`}
                      >
                        {form}: {n}
                      </button>
                    </li>
                  ))}
                </ul>
              </section>

              <section>
                <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--muted)]">
                  Top combination partners
                </h2>
                {report.top_combination_partners.length === 0 ? (
                  <p className="mt-2 text-sm text-[var(--muted)]">No co-ingredients in catalogue.</p>
                ) : (
                  <ol className="mt-2 space-y-1">
                    {report.top_combination_partners.map((p) => (
                      <li key={p.ingredient_id} className="text-sm">
                        <button
                          type="button"
                          className="text-[#087F6E] underline-offset-2 hover:underline"
                          onClick={() =>
                            pick({
                              id: p.ingredient_id,
                              canonical_name: p.canonical_name,
                            })
                          }
                        >
                          {p.canonical_name}
                        </button>
                        <span className="text-[var(--muted)]"> — in {p.product_count} products</span>
                      </li>
                    ))}
                  </ol>
                )}
              </section>

              <section>
                <div className="flex flex-wrap items-end justify-between gap-3">
                  <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--muted)]">
                    Brands ({report.total_filtered})
                  </h2>
                  <input
                    value={brandQ}
                    onChange={(e) => {
                      setBrandQ(e.target.value)
                      setPage(1)
                    }}
                    placeholder="Filter brands…"
                    className="rx-input px-3 py-2 text-xs"
                  />
                </div>
                <ul className="mt-3 space-y-2">
                  {report.products.map((p) => (
                    <li key={p.id} className="rx-card px-4 py-3 text-sm">
                      <div className="flex flex-wrap items-baseline justify-between gap-2">
                        <span className="font-semibold">{p.brand_name}</span>
                        <span className="font-mono text-xs text-[var(--muted)]">
                          {p.target_strength_value != null
                            ? `${p.target_strength_value}${p.target_strength_unit ? ` ${p.target_strength_unit}` : ''}`
                            : p.strength_label || '—'}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        {p.dosage_form || 'form unknown'}
                        {p.is_combination ? ' · combination' : ' · single-ingredient'}
                        {p.manufacturer ? ` · ${p.manufacturer}` : ''}
                      </p>
                      {p.incomplete_flag && (
                        <p className="mt-1 text-xs text-[#B45309]">
                          composition may be incomplete
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
                {report.total_pages > 1 && (
                  <div className="mt-4 flex items-center gap-3 text-sm">
                    <button
                      type="button"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-40"
                    >
                      Previous
                    </button>
                    <span className="text-[var(--muted)]">
                      Page {report.page} / {report.total_pages}
                    </span>
                    <button
                      type="button"
                      disabled={page >= report.total_pages}
                      onClick={() => setPage((p) => p + 1)}
                      className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-40"
                    >
                      Next
                    </button>
                  </div>
                )}
              </section>
            </div>
          )}
        </ErrorBoundary>
    </div>
    </AppLayout>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rx-card p-4">
      <p className="text-2xl font-bold tabular-nums text-[var(--heading)]">{value}</p>
      <p className="mt-1 text-xs text-[var(--muted)]">{label}</p>
    </div>
  )
}

export default IngredientsPage
