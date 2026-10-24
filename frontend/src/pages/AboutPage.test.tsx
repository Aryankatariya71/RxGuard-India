import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AboutPage } from './AboutPage'

describe('AboutPage', () => {
  it('links to methodology', () => {
    render(
      <MemoryRouter>
        <AboutPage />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('about-page')).toBeInTheDocument()
    const link = screen.getByTestId('about-methodology-link')
    expect(link).toHaveAttribute('href', '/methodology')
  })
})
