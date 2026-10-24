/**
 * Patient pill card schedule — derived ONLY from written frequency + dose on the Rx.
 * No indications, advice, or catalogue side-effect text.
 */

import type { LineItem } from '../api/types'
import { frequencyToHours } from './timeline'

export type PillSlot = 'morning' | 'afternoon' | 'evening' | 'night'

export const SLOT_LABELS_EN: Record<PillSlot, string> = {
  morning: 'Morning',
  afternoon: 'Afternoon',
  evening: 'Evening',
  night: 'Night',
}

export const SLOT_LABELS_HI: Record<PillSlot, string> = {
  morning: 'सुबह',
  afternoon: 'दोपहर',
  evening: 'शाम',
  night: 'रात',
}

export const SLOT_ORDER: PillSlot[] = ['morning', 'afternoon', 'evening', 'night']

export interface PillCardRow {
  brand: string
  ingredientsLabel: string
  doseLabel: string
  slots: Record<PillSlot, string | null>
  duration?: string
  frequencyNote?: string
}

export interface PillCardData {
  rows: PillCardRow[]
  asNeeded: { brand: string; instruction: string; ingredientsLabel: string }[]
  needsConfirmation: { line: string; reason: string }[]
  footer: string
}

const FOOTER =
  'This card only repeats what was written on the prescription. Ask your doctor or pharmacist if you are unsure.'

function hourToSlot(hour: number): PillSlot {
  if (hour <= 9) return 'morning'
  if (hour <= 14) return 'afternoon'
  if (hour <= 16) return 'evening'
  return 'night'
}

function parseDuration(line?: string): string | undefined {
  if (!line) return undefined
  const m = line.toLowerCase().match(/\bx\s*(\d+)\s*(day|days|d)\b/)
  return m ? `${m[1]} days` : undefined
}

function doseLabelFor(item: LineItem): string {
  if (item.dose_amount != null && item.dose_unit) {
    const u = item.dose_unit.toLowerCase()
    if (u === 'ml' || u.includes('ml')) return `${item.dose_amount} ml`
    if (u === 'mg' || u === 'g' || u === 'mcg') {
      // Strength per unit dose — show as 1 tablet/capsule carrying that strength when oral solid
      return `1 dose (${item.dose_amount} ${item.dose_unit})`
    }
    return `${item.dose_amount} ${item.dose_unit}`
  }
  if (item.dose_amount != null) return `${item.dose_amount}`
  return '1 tablet / dose as written'
}

function ingredientsLabel(item: LineItem): string {
  const parts = (item.ingredients || [])
    .map((ing) => {
      const n = ing.ingredient || '?'
      if (ing.strength_value != null) {
        return `${n} ${ing.strength_value}${ing.unit ? ` ${ing.unit}` : ''}`
      }
      return n
    })
    .filter(Boolean)
  return parts.join(' + ') || '—'
}

function extractFrequencyFromLine(line?: string): string | null {
  if (!line) return null
  const pattern = line.match(/\b(\d(?:-\d){1,3})\b/)
  if (pattern) return pattern[1]
  const code = line.match(/\b(OD|QD|BD|BID|TDS|TID|QID|QDS|HS|SOS|PRN)\b/i)
  return code ? code[1].toUpperCase() : null
}

export function buildPillCard(items: LineItem[]): PillCardData {
  const rows: PillCardRow[] = []
  const asNeeded: PillCardData['asNeeded'] = []
  const needsConfirmation: PillCardData['needsConfirmation'] = []

  for (const item of items || []) {
    const status = (item.status || '').toLowerCase()
    if (!item.resolved || status === 'ambiguous' || status === 'not_found') {
      needsConfirmation.push({
        line: item.line || item.matched_brand || 'Unknown line',
        reason: item.reason || status || 'Needs confirmation',
      })
      continue
    }

    const brand = item.matched_brand || item.line || 'Medicine'
    const freq =
      item.frequency_code ||
      extractFrequencyFromLine(item.line) ||
      null
    const prn = Boolean(item.prn) || /^(SOS|PRN)$/i.test(freq || '')
    const hours = frequencyToHours(freq, {
      prn,
      timesPerDay: item.times_per_day,
    })

    if (prn || hours === 'unclear') {
      if (prn || /sos|prn|as.?needed/i.test(item.line || '') || /sos|prn/i.test(freq || '')) {
        asNeeded.push({
          brand,
          instruction: (item.line || '').trim() || 'As needed (as written)',
          ingredientsLabel: ingredientsLabel(item),
        })
      } else {
        needsConfirmation.push({
          line: item.line || brand,
          reason: 'Schedule unclear from written frequency',
        })
      }
      continue
    }

    const dose = doseLabelFor(item)
    const slots: Record<PillSlot, string | null> = {
      morning: null,
      afternoon: null,
      evening: null,
      night: null,
    }
    for (const h of hours) {
      slots[hourToSlot(h)] = dose
    }

    rows.push({
      brand,
      ingredientsLabel: ingredientsLabel(item),
      doseLabel: dose,
      slots,
      duration: parseDuration(item.line),
      frequencyNote: freq || undefined,
    })
  }

  return { rows, asNeeded, needsConfirmation, footer: FOOTER }
}
