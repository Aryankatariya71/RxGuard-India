import { describe, expect, it } from 'vitest'
import { buildTimeline, frequencyToHours } from './timeline'
import type { Alert, DailyIngredient, LineItem } from '../api/types'

describe('frequencyToHours', () => {
  it('maps 1-0-1 to 8am and 9pm', () => {
    expect(frequencyToHours('1-0-1')).toEqual([8, 21])
  })
  it('maps TDS and 1-1-1 to three daytime slots', () => {
    expect(frequencyToHours('TDS')).toEqual([8, 14, 21])
    expect(frequencyToHours('1-1-1')).toEqual([8, 14, 21])
  })
  it('maps BD, OD, QID, HS', () => {
    expect(frequencyToHours('BD')).toEqual([8, 21])
    expect(frequencyToHours('OD')).toEqual([8])
    expect(frequencyToHours('QID')).toEqual([8, 12, 16, 21])
    expect(frequencyToHours('HS')).toEqual([22])
  })
  it('marks SOS/PRN unclear', () => {
    expect(frequencyToHours('SOS')).toBe('unclear')
    expect(frequencyToHours('OD', { prn: true })).toBe('unclear')
  })
})

describe('buildTimeline', () => {
  const items: LineItem[] = [
    {
      line: 'Tab A 1-0-1',
      matched_brand: 'Brand A',
      resolved: true,
      frequency_code: '1-0-1',
      ingredients: [{ ingredient: 'paracetamol', strength_value: 500, unit: 'mg' }],
    },
    {
      line: 'Tab B BD',
      matched_brand: 'Brand B',
      resolved: true,
      frequency_code: 'BD',
      ingredients: [{ ingredient: 'paracetamol', strength_value: 650, unit: 'mg' }],
    },
    {
      line: 'Tab C SOS',
      matched_brand: 'Brand C',
      resolved: true,
      frequency_code: 'SOS',
      prn: true,
    },
  ]
  const daily: DailyIngredient[] = [
    {
      ingredient: 'paracetamol',
      total_mg_per_day: 2300,
      unit: 'mg',
      contributions: [
        { brand: 'Brand A', mg_per_day: 1000 },
        { brand: 'Brand B', mg_per_day: 1300 },
      ],
    },
  ]
  const alerts: Alert[] = [
    {
      id: '1',
      type: 'dose',
      tier: 'critical',
      title: 'Dose',
      reason: 'x',
      suggested_action: 'y',
      ingredients: ['paracetamol'],
      brands: ['Brand A', 'Brand B'],
      source_rule_id: 'MAX-001',
      source_label: 'draft',
      limit_mg_day: 4000,
      total_mg_per_day: 2300,
    },
  ]

  it('builds doses and cumulative series from engine totals', () => {
    const t = buildTimeline(items, daily, alerts)
    expect(t.doses.length).toBeGreaterThanOrEqual(4)
    expect(t.unclear.some((u) => u.brand === 'Brand C')).toBe(true)
    expect(t.series).toHaveLength(1)
    expect(t.series[0].totalMgDay).toBe(2300)
    expect(t.series[0].limitMgDay).toBe(4000)
    expect(t.caption).toMatch(/Illustrative schedule/)
  })
})
