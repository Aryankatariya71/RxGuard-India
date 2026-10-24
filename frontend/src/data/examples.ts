import type { PatientFormState } from '../api/types'

export interface ExampleScenario {
  id: string
  title: string
  subtitle: string
  icon: 'layers' | 'alert' | 'baby' | 'droplets' | 'search' | 'kidney' | 'check'
  rx: string
  patient: PatientFormState
}

export const EXAMPLES: ExampleScenario[] = [
  {
    id: 'hidden-para',
    title: 'Hidden paracetamol duplication',
    subtitle: 'Three brands, one API — under the adult limit',
    icon: 'layers',
    rx: 'Tab Dolo 650 1-0-1 x 5 days\nTab Crocin Advance BD\nTab Combiflam 1-0-1',
    patient: { age_years: 35, weight_kg: 70, sex: 'M', kidney: 'normal', pregnant: false },
  },
  {
    id: 'adult-od',
    title: 'Adult overdose',
    subtitle: 'Stacked paracetamol exceeds 4 g/day',
    icon: 'alert',
    rx: 'Tab Dolo 650 1-1-1-1\nTab Crocin Advance QID\nTab Combiflam 1-1-1',
    patient: { age_years: 35, weight_kg: 70, sex: 'M', kidney: 'normal', pregnant: false },
  },
  {
    id: 'child-od',
    title: 'Child overdose',
    subtitle: 'Age 5 / 18 kg — weight-based limit shown',
    icon: 'baby',
    rx: 'Tab Dolo 650 TDS\nTab Crocin Advance BD',
    patient: { age_years: 5, weight_kg: 18, sex: 'M', kidney: 'unknown', pregnant: false },
  },
  {
    id: 'warfarin',
    title: 'Bleeding risk (warfarin + aspirin + ibuprofen)',
    subtitle: 'Three critical curated interaction pairs',
    icon: 'droplets',
    rx: 'Tab Warf 5 1-0-0\nTab Ecosprin 75 OD\nTab Brufen 400 TDS',
    patient: { age_years: 55, weight_kg: 70, sex: 'M', kidney: 'normal', pregnant: false },
  },
  {
    id: 'misspell',
    title: 'Misspelling + unknown brand',
    subtitle: 'Fuzzy match + never skip unresolved lines',
    icon: 'search',
    rx: 'Tab Dolo650 TDS\nTab Pantap 40 OD\nTab Xyzabc 1-0-1',
    patient: { age_years: 35, weight_kg: 70, sex: 'F', kidney: 'normal', pregnant: false },
  },
  {
    id: 'kidney-nsaid',
    title: 'Kidney patient on NSAID',
    subtitle: 'Severe renal band marks ibuprofen avoid',
    icon: 'kidney',
    rx: 'Tab Brufen 400 TDS',
    patient: { age_years: 55, weight_kg: 70, sex: 'M', kidney: 'severe', pregnant: false },
  },
  {
    id: 'clean',
    title: 'Clean prescription',
    subtitle: 'Therapeutic doses, no critical alerts',
    icon: 'check',
    rx: 'Tab Pantop 40 OD\nTab Amlong 5 OD',
    patient: { age_years: 40, weight_kg: 70, sex: 'M', kidney: 'normal', pregnant: false },
  },
]

/** Map UI kidney band → API egfr hint (pipeline uses renal_band via egfr). */
export function kidneyToEgfr(band: PatientFormState['kidney']): number | null {
  switch (band) {
    case 'normal':
      return 90
    case 'mild_moderate':
      return 45
    case 'severe':
      return 20
    default:
      return null
  }
}
