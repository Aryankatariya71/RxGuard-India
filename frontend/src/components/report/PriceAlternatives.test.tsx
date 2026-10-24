import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { PriceAlternatives } from './PriceAlternatives'
import type { LineItem } from '../../api/types'

describe('PriceAlternatives', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (String(url).includes('/alternatives')) {
          return {
            ok: true,
            json: async () => ({
              product_id: 'prod-demo-alpha',
              found: true,
              base_price: 100,
              price_as_of: '2022-11',
              alternatives: [
                {
                  id: 'prod-demo-alpha-cheap',
                  brand_name: 'Demo Product Alpha Value',
                  manufacturer: 'Synthetic Budget Labs',
                  price: 62.5,
                  price_as_of: '2022-11',
                  percent_difference: -37.5,
                },
              ],
              caveat:
                'Listed prices are from a 2022 dataset. Do not switch medicines without asking your doctor or pharmacist.',
              note: 'Informational only — not a recommendation to switch medicines.',
            }),
          }
        }
        if (String(url).includes('/medicines/search')) {
          return {
            ok: true,
            json: async () => ({
              exact: [{ id: 'prod-demo-alpha', brand_name: 'Demo Product Alpha' }],
              items: [],
            }),
          }
        }
        return { ok: false, json: async () => ({}) }
      }),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('smoke: shows lower-priced options and 2022 caveat', async () => {
    const item: LineItem = {
      line: 'Demo Product Alpha 1-0-1',
      matched_brand: 'Demo Product Alpha',
      resolved: true,
      brand_id: undefined,
      ingredients: [{ ingredient: 'Synthetic Ingredient X', strength_value: 500, unit: 'mg' }],
    }
    render(<PriceAlternatives item={item} />)
    await waitFor(() => {
      expect(screen.getByTestId('price-alternatives')).toBeInTheDocument()
    })
    expect(
      screen.getByText(/Lower-priced options with the same composition/i),
    ).toBeInTheDocument()
    expect(screen.getByText('Demo Product Alpha Value')).toBeInTheDocument()
    expect(screen.getByText(/2022 dataset/i)).toBeInTheDocument()
    expect(screen.queryByText(/recommend/i)).toBeInTheDocument()
  })

  it('renders nothing when unresolved', () => {
    const item: LineItem = {
      line: 'Unknown',
      matched_brand: null,
      resolved: false,
    }
    const { container } = render(<PriceAlternatives item={item} />)
    expect(container).toBeEmptyDOMElement()
  })
})
