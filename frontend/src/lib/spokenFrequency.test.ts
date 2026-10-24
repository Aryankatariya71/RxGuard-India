import { describe, expect, it } from 'vitest'
import {
  findSpokenFrequencyMatches,
  interpretedFrequencyForLine,
  normalizeSpokenFrequencies,
} from './spokenFrequency'

describe('spokenFrequency normaliser', () => {
  it('maps Hindi frequency phrases', () => {
    expect(normalizeSpokenFrequencies('Dolo 650 subah shaam').text).toContain('1-0-1')
    expect(normalizeSpokenFrequencies('Crocin teen baar').text).toContain('TDS')
    expect(normalizeSpokenFrequencies('Pantocid do baar').text).toContain('BD')
    expect(normalizeSpokenFrequencies('Thyronorm ek baar').text).toContain('OD')
    expect(normalizeSpokenFrequencies('Atorva raat ko').text).toContain('HS')
  })

  it('maps meal timing phrases', () => {
    expect(normalizeSpokenFrequencies('Pantop khali pet').text).toContain('AC')
    expect(normalizeSpokenFrequencies('Metformin khane ke baad').text).toContain('PC')
  })

  it('finds matches without rewriting when inspecting', () => {
    const m = findSpokenFrequencyMatches('Tab X teen baar khane ke baad')
    expect(m.some((x) => x.code === 'TDS')).toBe(true)
    expect(m.some((x) => x.code === 'PC')).toBe(true)
  })

  it('interpretedFrequencyForLine surfaces confirmation label', () => {
    expect(interpretedFrequencyForLine('something subah shaam')).toMatch(/1-0-1/)
    expect(interpretedFrequencyForLine('plain line')).toBeUndefined()
  })
})
