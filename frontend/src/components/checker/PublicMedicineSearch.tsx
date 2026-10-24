import { useState } from 'react'
import { Loader2, Search, Database } from 'lucide-react'

export type PublicHit = {
  name: string
  source_record_id?: string
  source?: string
  source_url?: string
  dosage_form?: string | null
  strength_label?: string | null
  ingredients?: { canonical_name?: string; name?: string; rxcui?: string }[]
  verification_status?: string
  geographic_applicability?: string
  match_type?: string
  similarity?: number | null
  note?: string
  tty?: string
}

interface Props {
  onInsertBrand: (brandName: string) => void
}

const LABEL: Record<string, string> = {
  SOURCE_BACKED: 'SOURCE_BACKED',
  PARTIALLY_VERIFIED: 'PARTIALLY_VERIFIED',
  DEMO_ONLY: 'DEMO_ONLY',
  UNRESOLVED: 'UNRESOLVED',
}

export function PublicMedicineSearch({ onInsertBrand }: Props) {
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [localItems, setLocalItems] = useState<PublicHit[]>([])
  const [rxItems, setRxItems] = useState<PublicHit[]>([])
  const [message, setMessage] = useState<string | null>(null)
  const [confirming, setConfirming] = useState<string | null>(null)

  const search = async () => {
    const query = q.trim()
    if (!query) return
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      const res = await fetch(
        `/api/medicines/search/combined?q=${encodeURIComponent(query)}&include_rxnorm=true`,
        { signal: AbortSignal.timeout(20000) },
      )
      if (!res.ok) throw new Error(`Search failed (${res.status})`)
      const data = await res.json()
      const local = (data.local?.items || []).map((i: Record<string, unknown>) => ({
        name: String(i.brand_name || i.name || ''),
        source_record_id: i.source_record_id as string | undefined,
        source: i.source as string | undefined,
        source_url: i.source_url as string | undefined,
        dosage_form: i.dosage_form as string | null,
        strength_label: (i.strength_label || i.strength) as string | null,
        ingredients: (i.ingredients as PublicHit['ingredients']) || [],
        verification_status: String(i.verification_status || (i.is_synthetic ? 'DEMO_ONLY' : 'UNRESOLVED')),
        geographic_applicability: i.geographic_applicability as string | undefined,
        match_type: i.match_type as string | undefined,
        similarity: i.similarity as number | null,
      }))
      const rx = (data.rxnorm?.items || []).map((i: Record<string, unknown>) => ({
        name: String(i.name || ''),
        source_record_id: String(i.source_record_id || ''),
        source: String(i.source || 'RxNorm'),
        source_url: i.source_url as string | undefined,
        dosage_form: i.dosage_form as string | null,
        strength_label: i.strength_label as string | null,
        ingredients: (i.ingredients as PublicHit['ingredients']) || [],
        verification_status: String(i.verification_status || 'SOURCE_BACKED'),
        geographic_applicability: String(i.geographic_applicability || 'US_RXNORM'),
        match_type: i.match_type as string | undefined,
        similarity: i.similarity as number | null,
        note: i.note as string | undefined,
        tty: i.tty as string | undefined,
      }))
      setLocalItems(local)
      setRxItems(rx)
      if (!local.length && !rx.length) {
        setMessage(data.message || 'No suitable match was found in the available sources.')
      }
    } catch (e) {
      setError((e as Error).message || 'Search failed')
      setLocalItems([])
      setRxItems([])
    } finally {
      setLoading(false)
    }
  }

  const confirmRxnorm = async (hit: PublicHit) => {
    if (!hit.source_record_id) return
    setConfirming(hit.source_record_id)
    setError(null)
    try {
      const res = await fetch('/api/external/rxnorm/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_record_id: hit.source_record_id,
          name: hit.name,
          source: hit.source,
          source_url: hit.source_url,
          dosage_form: hit.dosage_form,
          strength_label: hit.strength_label,
          ingredients: hit.ingredients,
          verification_status: hit.verification_status || 'SOURCE_BACKED',
          geographic_applicability: hit.geographic_applicability || 'US_RXNORM',
          tty: hit.tty,
          match_type: hit.match_type,
        }),
      })
      if (!res.ok) throw new Error(`Confirm failed (${res.status})`)
      onInsertBrand(hit.name)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setConfirming(null)
    }
  }

  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)]/50 p-4">
      <div className="mb-3 flex items-center gap-2">
        <Database className="h-4 w-4 text-teal-400" aria-hidden />
        <h3 className="text-sm font-bold">Search public medicine database</h3>
      </div>
      <p className="mb-3 text-xs text-[var(--muted)]">
        Local catalogue first, then live RxNorm (NLM). RxNorm is US terminology — not a complete
        Indian brand list. Confirm a hit before adding it to the prescription.
      </p>
      <div className="flex gap-2">
        <label className="sr-only" htmlFor="public-med-q">
          Medicine name
        </label>
        <input
          id="public-med-q"
          className="input flex-1"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && void search()}
          placeholder="e.g. paracetamol, ibuprofen, metformin"
        />
        <button
          type="button"
          className="btn-secondary inline-flex items-center gap-1.5 px-3"
          onClick={() => void search()}
          disabled={loading || !q.trim()}
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          Search
        </button>
      </div>

      {error && (
        <p className="mt-3 text-sm text-red-400" role="alert">
          {error}
        </p>
      )}
      {message && (
        <p className="mt-3 text-sm text-[var(--muted)]" role="status">
          {message}
        </p>
      )}

      {localItems.length > 0 && (
        <ResultGroup
          title="Local catalogue"
          items={localItems}
          confirming={confirming}
          onUse={(h) => onInsertBrand(h.name)}
        />
      )}
      {rxItems.length > 0 && (
        <ResultGroup
          title="RxNorm (public)"
          items={rxItems}
          confirming={confirming}
          onUse={(h) => void confirmRxnorm(h)}
          useLabel="Confirm & add"
        />
      )}
    </div>
  )
}

function ResultGroup({
  title,
  items,
  confirming,
  onUse,
  useLabel = 'Add to prescription',
}: {
  title: string
  items: PublicHit[]
  confirming: string | null
  onUse: (h: PublicHit) => void
  useLabel?: string
}) {
  return (
    <div className="mt-4">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">{title}</p>
      <ul className="space-y-2">
        {items.slice(0, 8).map((h) => {
          const status = LABEL[h.verification_status || ''] || h.verification_status || 'UNRESOLVED'
          const ings =
            h.ingredients
              ?.map((i) => i.canonical_name || i.name)
              .filter(Boolean)
              .join(', ') || 'Ingredients not supplied by source'
          return (
            <li
              key={`${h.source_record_id || h.name}-${h.match_type}`}
              className="rounded-xl border border-[var(--border)] p-3 text-sm"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-semibold">{h.name}</p>
                  <p className="mt-0.5 text-xs text-[var(--muted)]">
                    {[h.dosage_form, h.strength_label, h.match_type, h.tty]
                      .filter(Boolean)
                      .join(' · ')}
                    {h.similarity != null ? ` · score ${h.similarity}` : ''}
                  </p>
                  <p className="mt-1 text-xs">{ings}</p>
                  <p className="mt-1 text-[11px] text-[var(--muted)]">
                    Source: {h.source || 'source not recorded'}
                    {h.source_record_id ? ` · id ${h.source_record_id}` : ''}
                  </p>
                  {h.note && <p className="mt-1 text-[11px] text-amber-300/90">{h.note}</p>}
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className="rounded-full border border-teal-500/30 bg-teal-500/10 px-2 py-0.5 text-[10px] font-semibold text-teal-300">
                    {status}
                  </span>
                  <button
                    type="button"
                    className="btn-secondary text-xs"
                    disabled={confirming === h.source_record_id}
                    onClick={() => onUse(h)}
                  >
                    {confirming === h.source_record_id ? 'Saving…' : useLabel}
                  </button>
                </div>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
