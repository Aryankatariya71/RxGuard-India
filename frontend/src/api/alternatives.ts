export interface PriceAlternative {
  id: string
  brand_name: string
  manufacturer?: string | null
  price: number
  price_as_of?: string
  percent_difference?: number | null
  dosage_form?: string | null
  verification_status?: string | null
}

export interface AlternativesResponse {
  product_id: string
  brand_name?: string
  found: boolean
  base_price?: number | null
  price_as_of?: string
  alternatives: PriceAlternative[]
  caveat: string
  note?: string
  skipped_reason?: string
}

/** Resolve catalogue product id from analyze brand_id or brand name search. */
export function catalogueProductId(brandId?: number | null): string | null {
  if (brandId == null || Number.isNaN(Number(brandId))) return null
  return `cat-${brandId}`
}

export async function fetchAlternatives(
  medicineId: string,
  limit = 3,
): Promise<AlternativesResponse | null> {
  try {
    const res = await fetch(
      `/api/medicines/${encodeURIComponent(medicineId)}/alternatives?limit=${limit}`,
      { signal: AbortSignal.timeout(8000) },
    )
    if (!res.ok) return null
    return (await res.json()) as AlternativesResponse
  } catch {
    return null
  }
}

export async function resolveMedicineIdForAlternatives(opts: {
  brandId?: number | null
  matchedBrand?: string | null
}): Promise<string | null> {
  const fromId = catalogueProductId(opts.brandId)
  if (fromId) {
    const probe = await fetchAlternatives(fromId, 1)
    if (probe?.found) return fromId
  }
  const name = (opts.matchedBrand || '').trim()
  if (!name) return null
  try {
    const res = await fetch(
      `/api/medicines/search?q=${encodeURIComponent(name)}&limit=5`,
      { signal: AbortSignal.timeout(8000) },
    )
    if (!res.ok) return null
    const body = (await res.json()) as {
      exact?: { id: string; brand_name?: string }[]
      items?: { id: string; brand_name?: string }[]
    }
    const pool = [...(body.exact || []), ...(body.items || [])]
    const exact = pool.find(
      (p) => (p.brand_name || '').toLowerCase() === name.toLowerCase(),
    )
    return exact?.id || pool[0]?.id || null
  } catch {
    return null
  }
}
