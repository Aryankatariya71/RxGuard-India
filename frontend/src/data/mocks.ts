import type { AnalyzeResponse, PatientFormState } from '../api/types'
import mockJson from './mock_responses.json'

const MOCKS = mockJson as Record<string, AnalyzeResponse>

export function getMockResponse(
  exampleId: string | null | undefined,
  prescription_text: string,
  _patient: PatientFormState,
): AnalyzeResponse {
  if (exampleId && MOCKS[exampleId]) {
    return structuredClone(MOCKS[exampleId])
  }
  // Fuzzy match by first line
  const first = (prescription_text || '').split('\n')[0]?.trim().toLowerCase() || ''
  for (const [id, data] of Object.entries(MOCKS)) {
    const sample = EXAMPLES_RX[id]?.split('\n')[0]?.trim().toLowerCase()
    if (sample && first && (first.includes(sample.slice(0, 12)) || sample.includes(first.slice(0, 12)))) {
      return structuredClone(data)
    }
  }
  return {
    empty: !prescription_text.trim(),
    items: [],
    daily_doses: { by_ingredient: [], strength_unclear: [] },
    alerts: [
      {
        id: 'OFFLINE',
        type: 'needs_confirmation',
        tier: 'info',
        title: 'Offline demo mode',
        reason:
          'API unreachable. Load an example scenario to see bundled demo data, or start uvicorn on port 8000.',
        suggested_action: 'Run ./run_demo.sh or pick an example card.',
        ingredients: [],
        brands: [],
        source_rule_id: 'OFFLINE',
        source_label: 'offline_demo',
      },
    ],
    counts: { critical: 0, review: 0, info: 1 },
    verdict: 'review',
  }
}

const EXAMPLES_RX: Record<string, string> = {
  'hidden-para': 'Tab Dolo 650 1-0-1 x 5 days',
  'adult-od': 'Tab Dolo 650 1-1-1-1',
  'child-od': 'Tab Dolo 650 TDS',
  warfarin: 'Tab Warf 5 1-0-0',
  misspell: 'Tab Dolo650 TDS',
  'kidney-nsaid': 'Tab Brufen 400 TDS',
  clean: 'Tab Pantop 40 OD',
}

export function hasMockFor(exampleId: string) {
  return Boolean(MOCKS[exampleId])
}
