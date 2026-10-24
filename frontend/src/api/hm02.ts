/** Typed client for the HM-02 backend (backend.app.main). */

const BASE = import.meta.env.VITE_API_BASE_URL || '/api'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const j = await res.json()
      detail = j.detail || JSON.stringify(j)
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return res.json()
  return res.text() as unknown as T
}

export const api = {
  health: () => req<{ status: string; database: string }>('/health'),
  config: () =>
    req<{
      app_name: string
      demo_data_mode: boolean
      catalogue_version: string
      rule_set_version: string
      disclaimer: string
      auth_enabled: boolean
    }>('/config/public'),
  medicines: (params: Record<string, string | number | undefined>) => {
    const q = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '') q.set(k, String(v))
    })
    return req<{ items: Medicine[]; total: number }>(`/medicines?${q}`)
  },
  medicine: (id: string) => req<Medicine>(`/medicines/${id}`),
  createReview: (body: object) => req<Review>('/reviews', { method: 'POST', body: JSON.stringify(body) }),
  listReviews: (params: Record<string, string | number | undefined> = {}) => {
    const q = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '') q.set(k, String(v))
    })
    return req<{ items: Review[]; total: number }>(`/reviews?${q}`)
  },
  getReview: (id: string) => req<Review>(`/reviews/${id}`),
  updateReview: (id: string, body: object) =>
    req<Review>(`/reviews/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteReview: (id: string) => req<{ ok: boolean }>(`/reviews/${id}`, { method: 'DELETE' }),
  addItem: (id: string, body: object) =>
    req<ReviewItem>(`/reviews/${id}/items`, { method: 'POST', body: JSON.stringify(body) }),
  updateItem: (rid: string, iid: string, body: object) =>
    req<ReviewItem>(`/reviews/${rid}/items/${iid}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  deleteItem: (rid: string, iid: string) =>
    req<{ ok: boolean }>(`/reviews/${rid}/items/${iid}`, { method: 'DELETE' }),
  evaluate: (id: string) => req<Report>(`/reviews/${id}/evaluate`, { method: 'POST' }),
  report: (id: string) => req<Report>(`/reviews/${id}/report`),
  exportUrl: (id: string, format: 'txt' | 'csv' = 'txt') =>
    `${BASE}/reviews/${id}/export?format=${format}`,
  dataStatus: () => req<Record<string, unknown>>('/data/status'),
  rulesStatus: () => req<Record<string, unknown>>('/rules/status'),
  demoScenario: (id: string) =>
    req<{ scenario_id: string; label: string; review: Review; report: Report }>(
      `/demo/scenarios/${id}`,
      { method: 'POST' },
    ),
}

export interface Ingredient {
  id: string
  canonical_name: string
  is_synthetic?: boolean
  ingredient_strength?: number
  strength_unit?: string
}

export interface Medicine {
  id: string
  brand_name: string
  generic_display_name?: string
  strength?: string
  dosage_form?: string
  route?: string
  manufacturer?: string | null
  catalogue_status: string
  source_name: string
  is_synthetic: boolean
  ingredients: Ingredient[]
}

export interface ReviewItem {
  id: string
  product_id?: string | null
  entered_brand_name: string
  dose_amount?: number | null
  dose_unit?: string | null
  frequency_value?: number | null
  frequency_unit?: string | null
  route?: string | null
  resolution_status: string
  product?: Medicine | null
  candidates?: Medicine[]
}

export interface Review {
  id: string
  review_reference: string
  title?: string | null
  patient_reference?: string | null
  age_years?: number | null
  status: string
  item_count?: number
  finding_count?: number
  summary?: Record<string, unknown> | null
  items?: ReviewItem[]
  created_at?: string
  catalogue_version?: string
  rule_set_version?: string
}

export interface Finding {
  id: string
  finding_code: string
  category: string
  severity: string
  title: string
  description: string
  affected_brand_names: string[]
  evidence_status: string
  source_reference?: string | null
  rule_id?: string | null
  rule_version?: string | null
  is_synthetic: boolean
  limitations?: string | null
  recommended_next_step?: string | null
  evaluation_status: string
  created_at?: string
}

export interface Report {
  review: Review
  items: ReviewItem[]
  findings: Finding[]
  summary: Record<string, unknown>
  severity_counts: Record<string, number>
  disclaimer: string
}
