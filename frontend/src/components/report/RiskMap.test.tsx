import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RiskMap } from './RiskMap'
import type { AnalyzeResponse } from '../../api/types'

describe('RiskMap', () => {
  it('smoke: shows empty message when no edges', () => {
    const report: AnalyzeResponse = {
      items: [
        {
          line: 'x',
          matched_brand: 'Solo',
          resolved: true,
          ingredients: [{ ingredient: 'X', strength_value: 1, unit: 'mg' }],
        },
      ],
      daily_doses: { by_ingredient: [], strength_unclear: [] },
      alerts: [],
      counts: { critical: 0, review: 0, info: 0 },
      verdict: 'clear',
    }
    render(<RiskMap report={report} />)
    expect(screen.getByTestId('risk-map')).toBeInTheDocument()
    expect(
      screen.getByText('No matching rule in this prototype dataset'),
    ).toBeInTheDocument()
  })
})
