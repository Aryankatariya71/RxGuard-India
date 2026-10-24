import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { StressTestPage } from './StressTestPage'

vi.mock('../hooks/useTheme', () => ({
  useTheme: () => ({ theme: 'dark' as const, toggle: () => undefined }),
}))

describe('StressTestPage', () => {
  it('smoke: renders controls', () => {
    render(
      <MemoryRouter>
        <StressTestPage />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('stress-test-page')).toBeInTheDocument()
    expect(screen.getByText(/Run synthetic prescriptions/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^Run$/i })).toBeInTheDocument()
  })
})
