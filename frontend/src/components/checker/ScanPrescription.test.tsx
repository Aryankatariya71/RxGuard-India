import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ScanPrescription } from './ScanPrescription'

vi.mock('../../lib/ocrLocal', () => ({
  recognizeImageLocal: vi.fn(async () => 'Tab Demo Product Alpha 1-0-1'),
}))

describe('ScanPrescription', () => {
  it('smoke: shows scan and sample buttons plus offline note', () => {
    render(<ScanPrescription onUseText={() => undefined} />)
    expect(screen.getByTestId('scan-prescription')).toBeInTheDocument()
    expect(screen.getByText(/Scan prescription/i)).toBeInTheDocument()
    expect(screen.getByText(/Try printed sample/i)).toBeInTheDocument()
    expect(screen.getByText(/never uploaded/i)).toBeInTheDocument()
  })
})
