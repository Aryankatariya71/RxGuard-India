import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PillCard } from './PillCard'
import type { AnalyzeResponse } from '../../api/types'

describe('PillCard', () => {
  it('smoke: renders grid and footer caveat', () => {
    const report: AnalyzeResponse = {
      items: [
        {
          line: 'Tab Demo 1-0-1 x 5 days',
          matched_brand: 'Demo Product Alpha',
          resolved: true,
          frequency_code: '1-0-1',
          dose_amount: 1,
          dose_unit: 'tablet',
          ingredients: [{ ingredient: 'Synthetic Ingredient X', strength_value: 500, unit: 'mg' }],
        },
      ],
      daily_doses: { by_ingredient: [], strength_unclear: [] },
      alerts: [],
      counts: { critical: 0, review: 0, info: 0 },
      verdict: 'clear',
    }
    render(<PillCard report={report} />)
    expect(screen.getByTestId('pill-card')).toBeInTheDocument()
    expect(screen.getByText('Demo Product Alpha')).toBeInTheDocument()
    expect(screen.getByText(/only repeats what was written/i)).toBeInTheDocument()
  })
})
