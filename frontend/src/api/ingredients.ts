export interface IngredientHit {
  id: string
  canonical_name: string
  normalized_name?: string
  status?: string
}

export interface IngredientProductItem {
  id: string
  brand_name: string
  manufacturer?: string | null
  dosage_form?: string | null
  strength_label?: string | null
  ingredient_count: number
  is_combination: boolean
  incomplete_flag: boolean
  composition_note?: string | null
  target_strength_value?: number | null
  target_strength_unit?: string | null
}

export interface IngredientProductsResponse {
  found: boolean
  ingredient: {
    id: string
    canonical_name: string
    normalized_name?: string
  }
  total_products: number
  by_dosage_form: Record<string, number>
  single_ingredient: number
  combination: number
  top_combination_partners: {
    ingredient_id: string
    canonical_name: string
    product_count: number
  }[]
  products: IngredientProductItem[]
  page: number
  page_size: number
  total_filtered: number
  total_pages: number
  caption: string
}

export async function searchIngredients(q: string, limit = 20): Promise<IngredientHit[]> {
  if (!q.trim()) return []
  try {
    const res = await fetch(
      `/api/ingredients/search?q=${encodeURIComponent(q)}&limit=${limit}`,
      { signal: AbortSignal.timeout(8000) },
    )
    if (!res.ok) return []
    const body = (await res.json()) as { items?: IngredientHit[] }
    return body.items || []
  } catch {
    return []
  }
}

export async function fetchIngredientProducts(
  id: string,
  params: {
    page?: number
    page_size?: number
    q?: string
    dosage_form?: string
    combination_only?: boolean | null
  } = {},
): Promise<IngredientProductsResponse | null> {
  const sp = new URLSearchParams()
  sp.set('page', String(params.page ?? 1))
  sp.set('page_size', String(params.page_size ?? 50))
  if (params.q) sp.set('q', params.q)
  if (params.dosage_form) sp.set('dosage_form', params.dosage_form)
  if (params.combination_only === true) sp.set('combination_only', 'true')
  if (params.combination_only === false) sp.set('combination_only', 'false')
  try {
    const res = await fetch(`/api/ingredients/${encodeURIComponent(id)}/products?${sp}`, {
      signal: AbortSignal.timeout(15000),
    })
    if (!res.ok) return null
    return (await res.json()) as IngredientProductsResponse
  } catch {
    return null
  }
}
