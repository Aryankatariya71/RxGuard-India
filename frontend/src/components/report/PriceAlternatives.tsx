import { useEffect, useState } from 'react'
import type { LineItem } from '../../api/types'
import {
  fetchAlternatives,
  resolveMedicineIdForAlternatives,
  type AlternativesResponse,
} from '../../api/alternatives'

interface Props {
  item: LineItem
}

export function PriceAlternatives({ item }: Props) {
  const [data, setData] = useState<AlternativesResponse | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    if (!item.resolved || !item.matched_brand) {
      setData(null)
      return
    }
    setLoading(true)
    ;(async () => {
      const id = await resolveMedicineIdForAlternatives({
        brandId: item.brand_id,
        matchedBrand: item.matched_brand,
      })
      if (!id || cancelled) {
        if (!cancelled) {
          setData(null)
          setLoading(false)
        }
        return
      }
      const alt = await fetchAlternatives(id, 3)
      if (!cancelled) {
        setData(alt)
        setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [item.brand_id, item.matched_brand, item.resolved])

  if (!item.resolved || !item.matched_brand) return null
  if (loading) {
    return (
      <div className="mt-3 rounded-xl border border-[var(--card-border)] bg-[#F8FBFA] px-3 py-2 text-[11px] text-[var(--muted)]">
        Looking up listed-price options…
      </div>
    )
  }
  if (!data?.found || !(data.alternatives || []).length) return null

  return (
    <div
      className="mt-3 rounded-xl border border-[#DCE8E4] bg-[#F0FDF4] px-3 py-3"
      data-testid="price-alternatives"
    >
      <h4 className="text-xs font-bold uppercase tracking-wider text-[#123C38]">
        Lower-priced options with the same composition
      </h4>
      <ul className="mt-2 space-y-2">
        {data.alternatives.map((a) => (
          <li
            key={a.id}
            className="flex flex-wrap items-baseline justify-between gap-2 text-sm"
          >
            <div>
              <span className="font-medium">{a.brand_name}</span>
              {a.manufacturer && (
                <span className="ml-1 text-[11px] text-[var(--muted)]">
                  · {a.manufacturer}
                </span>
              )}
            </div>
            <div className="font-mono text-xs">
              ₹{Number(a.price).toFixed(2)}
              <span className="ml-1 text-[10px] text-[var(--muted)]">
                ({a.price_as_of || data.price_as_of || '2022-11'})
              </span>
              {typeof a.percent_difference === 'number' && (
                <span
                  className={
                    a.percent_difference < 0
                      ? 'ml-1 text-[#15803D]'
                      : 'ml-1 text-[var(--muted)]'
                  }
                >
                  {a.percent_difference > 0 ? '+' : ''}
                  {a.percent_difference}%
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-[11px] leading-relaxed text-[#B45309]">
        {data.caveat}
      </p>
      {data.note && (
        <p className="mt-1 text-[10px] text-[var(--muted)]">{data.note}</p>
      )}
    </div>
  )
}
