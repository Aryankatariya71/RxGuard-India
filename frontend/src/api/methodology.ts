/** Live methodology / meta / evaluation fetches — never hard-code counts. */

export type MethodologyStats = {
  app_name?: string
  app_version?: string | null
  engine_version?: string | null
  dataset_version?: string | null
  catalogue_version?: string | null
  rule_set_version?: string | null
  demo_mode?: boolean
  products_in_db?: number | null
  ingredients_in_db?: number | null
  incomplete_composition_links?: number | null
  catalogue_files?: {
    source_csv_rows?: number | null
    cleaned_parquet_rows?: number | null
    ddinter_pairs_loaded?: number | null
  } | null
  interaction_rules?: {
    by_status?: Record<string, number | null> | null
    by_severity?: Record<string, number> | null
    active?: number | null
    synthetic?: number | null
  } | null
  dose_rules?: {
    by_status?: Record<string, number | null> | null
    active?: number | null
    synthetic?: number | null
  } | null
  ddinter_pairs_loaded?: number | null
  tests?: {
    backend_test_function_count?: number | null
    backend_test_file_count?: number | null
  } | null
  gold?: {
    gold_case_count?: number | null
    developer_labeled_count?: number | null
    pharmacist_verified_count?: number | null
    composition?: Record<string, number> | null
  } | null
  evaluation?: {
    brand_resolution_accuracy?: number | null
    brand_resolution_hits?: number | null
    brand_resolution_total?: number | null
    false_alarm_rate_clean?: number | null
    false_alarm_count?: number | null
    clean_case_count?: number | null
    avg_alerts_per_prescription?: number | null
    precision_recall_by_type?: Array<{
      type: string
      precision: number
      recall: number
      tp: number
      fp: number
      fn: number
    }> | null
    disclaimer?: string
    report_path?: string
  } | null
  composition_examples?: Array<{
    brand_name: string
    before: string
    after: string[]
    ingredient_count: number
    incomplete_flag?: boolean
    verification_status?: string
  }> | null
  alert_fatigue?: {
    naive_alert_count?: number | null
    merged_alert_count?: number | null
    note?: string
    stress_test_path?: string
  } | null
  disclaimer?: string
  rule_status_note?: string
}

export function formatStat(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return 'not available'
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value.toLocaleString()
  }
  return String(value)
}

export async function fetchMethodologyStats(): Promise<MethodologyStats | null> {
  try {
    const res = await fetch('/api/methodology/stats', {
      signal: AbortSignal.timeout(12000),
    })
    if (!res.ok) return null
    return (await res.json()) as MethodologyStats
  } catch {
    return null
  }
}

export async function searchMedicineLive(q: string) {
  const res = await fetch(`/api/medicines/search?q=${encodeURIComponent(q)}&limit=8`, {
    signal: AbortSignal.timeout(10000),
  })
  if (!res.ok) throw new Error(`Search failed (${res.status})`)
  return res.json()
}

export async function analyzeLiveExample(prescription_text: string) {
  const res = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prescription_text,
      patient: { age_years: 35, weight_kg: 70, sex: null, conditions: [] },
    }),
    signal: AbortSignal.timeout(25000),
  })
  if (!res.ok) throw new Error(`Analyze failed (${res.status})`)
  return res.json()
}
