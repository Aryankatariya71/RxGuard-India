/** Exact shapes from src/pipeline.analyze / POST /analyze */

export interface PatientIn {
  age_years: number
  weight_kg?: number | null
  sex?: string | null
  creatinine_mg_dl?: number | null
  egfr?: number | null
  pregnant?: boolean | null
  conditions?: string[]
}

export interface AnalyzeRequest {
  prescription_text: string
  patient: PatientIn
}

export interface Ingredient {
  ingredient?: string
  strength_value?: number | null
  unit?: string | null
  per_value?: number | null
  per_unit?: string | null
  raw?: string
  strength_missing?: boolean
  per_unit_missing?: boolean
  parse_error?: boolean
  [key: string]: unknown
}

export interface Candidate {
  brand_id?: number
  name?: string
  score?: number
  [key: string]: unknown
}

export interface LineItem {
  line?: string
  matched_brand?: string | null
  status?: string
  ingredients?: Ingredient[]
  brand_id?: number
  resolved?: boolean
  candidates?: Candidate[]
  reason?: string
  frequency_code?: string | null
  times_per_day?: number | null
  prn?: boolean
  dose_amount?: number | null
  dose_unit?: string | null
}

export interface DoseContribution {
  brand: string
  mg_per_day: number
  assumed_max?: boolean
  duration_days?: number
}

export interface DailyIngredient {
  ingredient: string
  total_mg_per_day: number
  unit: string
  contributions: DoseContribution[]
}

export interface StrengthUnclear {
  ingredient?: string
  brand?: string
  reason?: string
  raw?: string
}

export interface Alert {
  id: string
  type: string
  tier: 'critical' | 'review' | 'info' | string
  title: string
  reason: string
  suggested_action: string
  ingredients: string[]
  brands: string[]
  source_rule_id: string
  source_label: string
  total_mg_per_day?: number
  limit_mg_day?: number
  percent?: number
  mechanism?: string
  [key: string]: unknown
}

export interface AnalyzeResponse {
  empty?: boolean
  items: LineItem[]
  resolved?: Record<string, unknown>[]
  needs_confirmation?: Record<string, unknown>[]
  daily_doses: {
    by_ingredient: DailyIngredient[]
    strength_unclear: StrengthUnclear[]
  }
  alerts: Alert[]
  counts: {
    critical: number
    review: number
    info: number
  }
  verdict: 'action_needed' | 'review' | 'clear' | string
  patient?: PatientIn & Record<string, unknown>
}

export type KidneyBand = 'normal' | 'mild_moderate' | 'severe' | 'unknown'

export interface PatientFormState {
  age_years: number
  weight_kg: number | null
  sex: '' | 'M' | 'F'
  kidney: KidneyBand
  pregnant: boolean
}
