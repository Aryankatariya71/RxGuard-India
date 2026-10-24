import type { AnalyzeRequest, AnalyzeResponse, PatientFormState } from './types'
import { kidneyToEgfr } from '../data/examples'
import { getMockResponse } from '../data/mocks'

export function toAnalyzeRequest(
  prescription_text: string,
  patient: PatientFormState,
): AnalyzeRequest {
  const egfr = kidneyToEgfr(patient.kidney)
  return {
    prescription_text,
    patient: {
      age_years: patient.age_years,
      weight_kg: patient.weight_kg,
      sex: patient.sex || null,
      egfr,
      pregnant: patient.pregnant,
      conditions: [],
    },
  }
}

export interface AnalyzeResult {
  data: AnalyzeResponse
  offline: boolean
}

export async function analyzePrescription(
  prescription_text: string,
  patient: PatientFormState,
  exampleId?: string | null,
): Promise<AnalyzeResult> {
  const body = toAnalyzeRequest(prescription_text, patient)
  try {
    const ctrl = new AbortController()
    const timer = setTimeout(() => ctrl.abort(), 25000)
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    })
    clearTimeout(timer)
    if (!res.ok) throw new Error(`API ${res.status}`)
    const data = (await res.json()) as AnalyzeResponse
    return { data, offline: false }
  } catch {
    const mock = getMockResponse(exampleId, prescription_text, patient)
    return { data: mock, offline: true }
  }
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch('/api/health', { signal: AbortSignal.timeout(3000) })
    return res.ok
  } catch {
    return false
  }
}
