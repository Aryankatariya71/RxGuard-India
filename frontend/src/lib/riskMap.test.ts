import { describe, expect, it } from 'vitest'
import { buildRiskMap } from './riskMap'
import type { Alert, LineItem } from '../api/types'

const items: LineItem[] = [
  {
    line: 'A',
    matched_brand: 'BrandA',
    resolved: true,
    ingredients: [{ ingredient: 'Warfarin', strength_value: 5, unit: 'mg' }],
  },
  {
    line: 'B',
    matched_brand: 'BrandB',
    resolved: true,
    ingredients: [{ ingredient: 'Ibuprofen', strength_value: 400, unit: 'mg' }],
  },
  {
    line: 'C',
    matched_brand: 'BrandC',
    resolved: true,
    ingredients: [{ ingredient: 'Paracetamol', strength_value: 500, unit: 'mg' }],
  },
  {
    line: 'D',
    matched_brand: 'BrandD',
    resolved: true,
    ingredients: [{ ingredient: 'Paracetamol', strength_value: 650, unit: 'mg' }],
  },
]

describe('buildRiskMap', () => {
  it('builds interaction edges with severity colour tier', () => {
    const alerts: Alert[] = [
      {
        id: '1',
        type: 'interaction',
        tier: 'critical',
        title: 'Warfarin + NSAID',
        reason: 'bleeding risk',
        suggested_action: 'review',
        ingredients: ['Warfarin', 'Ibuprofen'],
        brands: ['BrandA', 'BrandB'],
        source_rule_id: 'CURATED-001',
        source_label: 'curated_interactions',
        mechanism: 'additive bleeding risk',
      },
    ]
    const map = buildRiskMap(items, alerts)
    expect(map.edges).toHaveLength(1)
    expect(map.edges[0].kind).toBe('interaction')
    expect(map.edges[0].tier).toBe('critical')
    expect(map.edges[0].dashed).toBe(false)
    expect(map.edges[0].ruleId).toBe('CURATED-001')
    expect(map.edges[0].mechanism).toMatch(/bleeding/i)
    expect(map.emptyMessage).toBeUndefined()
  })

  it('marks duplicate edges as dashed self-loops', () => {
    const alerts: Alert[] = [
      {
        id: '2',
        type: 'duplicate',
        tier: 'review',
        title: 'Duplicate paracetamol',
        reason: 'same ingredient',
        suggested_action: 'review',
        ingredients: ['Paracetamol'],
        brands: ['BrandC', 'BrandD'],
        source_rule_id: 'DUP-PARA',
        source_label: 'duplicate_check',
      },
    ]
    const map = buildRiskMap(items, alerts)
    const dup = map.edges.find((e) => e.kind === 'duplicate')
    expect(dup?.dashed).toBe(true)
    expect(dup?.selfLoop).toBe(true)
  })

  it('accepts duplicate_dose alert type', () => {
    const alerts: Alert[] = [
      {
        id: '3',
        type: 'duplicate_dose',
        tier: 'critical',
        title: 'Duplicate + dose',
        reason: 'same ingredient over limit',
        suggested_action: 'review',
        ingredients: ['Paracetamol'],
        brands: ['BrandC', 'BrandD'],
        source_rule_id: 'MAX-001',
        source_label: 'merged:duplicate+dose',
      },
    ]
    const map = buildRiskMap(items, alerts)
    expect(map.edges.some((e) => e.kind === 'duplicate' && e.dashed)).toBe(true)
  })

  it('no-edge case message', () => {
    const map = buildRiskMap(items, [])
    expect(map.edges).toHaveLength(0)
    expect(map.emptyMessage).toBe('No matching rule in this prototype dataset')
  })
})
