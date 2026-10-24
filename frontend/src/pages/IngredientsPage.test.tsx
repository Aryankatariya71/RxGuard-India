import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { IngredientsPage } from './IngredientsPage'

vi.mock('../hooks/useTheme', () => ({
  useTheme: () => ({ theme: 'dark' as const, toggle: () => undefined }),
}))

describe('IngredientsPage', () => {
  it('smoke: renders finder heading and search', () => {
    render(
      <MemoryRouter>
        <IngredientsPage />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('ingredients-page')).toBeInTheDocument()
    expect(screen.getAllByText(/Hidden ingredient finder/i).length).toBeGreaterThan(0)
    expect(screen.getByLabelText(/Search ingredient/i)).toBeInTheDocument()
  })
})
