import { describe, expect, it } from 'vitest'
import { buildPillCard } from './pillCard'
import type { LineItem } from '../api/types'

function item(partial: Partial<LineItem>): LineItem {
  return {
    line: partial.line || 'Tab X',
    matched_brand: partial.matched_brand || 'BrandX',
    resolved: partial.resolved ?? true,
    status: partial.status || 'exact',
    ingredients: partial.ingredients || [
      { ingredient: 'Ing', strength_value: 500, unit: 'mg' },
    ],
    frequency_code: partial.frequency_code,
    times_per_day: partial.times_per_day,
    prn: partial.prn,
    dose_amount: partial.dose_amount ?? 1,
    dose_unit: partial.dose_unit ?? 'tablet',
    reason: partial.reason,
  }
}

describe('buildPillCard', () => {
  it('maps 1-0-1 to morning and night', () => {
    const card = buildPillCard([
      item({ frequency_code: '1-0-1', matched_brand: 'Dolo', dose_amount: 1, dose_unit: 'tablet' }),
    ])
    expect(card.rows).toHaveLength(1)
    expect(card.rows[0].slots.morning).toBeTruthy()
    expect(card.rows[0].slots.afternoon).toBeNull()
    expect(card.rows[0].slots.evening).toBeNull()
    expect(card.rows[0].slots.night).toBeTruthy()
  })

  it('maps TDS to morning, afternoon, night', () => {
    const card = buildPillCard([item({ frequency_code: 'TDS' })])
    const s = card.rows[0].slots
    expect(s.morning).toBeTruthy()
    expect(s.afternoon).toBeTruthy()
    expect(s.evening).toBeNull()
    expect(s.night).toBeTruthy()
  })

  it('maps QID to four slots', () => {
    const card = buildPillCard([item({ frequency_code: 'QID' })])
    const s = card.rows[0].slots
    expect(s.morning && s.afternoon && s.evening && s.night).toBeTruthy()
  })

  it('maps HS to night only', () => {
    const card = buildPillCard([item({ frequency_code: 'HS' })])
    const s = card.rows[0].slots
    expect(s.morning).toBeNull()
    expect(s.night).toBeTruthy()
  })

  it('puts SOS under as needed with written instruction', () => {
    const card = buildPillCard([
      item({
        line: 'Tab PainSOS SOS if headache',
        frequency_code: 'SOS',
        prn: true,
        matched_brand: 'PainSOS',
      }),
    ])
    expect(card.rows).toHaveLength(0)
    expect(card.asNeeded).toHaveLength(1)
    expect(card.asNeeded[0].instruction).toMatch(/SOS if headache/i)
  })

  it('puts unresolved under needs confirmation', () => {
    const card = buildPillCard([
      item({
        resolved: false,
        status: 'ambiguous',
        line: 'Tab Mystery',
        matched_brand: undefined,
        reason: 'ambiguous match',
      }),
    ])
    expect(card.needsConfirmation).toHaveLength(1)
    expect(card.needsConfirmation[0].line).toMatch(/Mystery/)
  })
})
