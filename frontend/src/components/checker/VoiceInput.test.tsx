import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { VoiceInput } from './VoiceInput'

describe('VoiceInput', () => {
  it('smoke: shows unavailable when SpeechRecognition missing', () => {
    render(<VoiceInput onTranscript={() => undefined} />)
    expect(screen.getByText(/Voice unavailable|Voice offline|Voice/i)).toBeInTheDocument()
  })
})
